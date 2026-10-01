"""
Thesis research pipeline.

Step 1  Map the company ecosystem (one Exa search with outputSchema).
Step 2  Run one Exa search per thesis dimension in parallel. Each search uses
        outputSchema so Exa synthesizes grounded signals (headline, impact,
        thesis impact, direction) directly from the sources it retrieved.

Every step emits events onto an in-memory bus so the UI can render the
research trace live. The full event log is persisted so a finished run can be
replayed exactly.
"""

import asyncio
import hashlib
import logging
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.database import SessionLocal
from app.models.research import ResearchRun
from app.services.exa.client import EXA_BASE_URL, get_exa_headers

logger = logging.getLogger(__name__)

SEARCH_MODES = [
    {"value": "instant", "label": "Instant", "description": "Lowest latency, real-time lookups", "latency": "<1s"},
    {"value": "fast", "label": "Fast", "description": "High quality with reduced latency", "latency": "~1s"},
    {"value": "auto", "label": "Auto", "description": "Balanced quality and speed (recommended)", "latency": "~1-2s"},
    {"value": "deep-lite", "label": "Deep Lite", "description": "Lightweight multi-query research", "latency": "~4s"},
    {"value": "deep", "label": "Deep", "description": "Comprehensive multi-step research", "latency": "~10-30s"},
    {"value": "deep-reasoning", "label": "Deep Reasoning", "description": "Strongest reasoning for complex analysis", "latency": "~30s+"},
]
VALID_MODES = {m["value"] for m in SEARCH_MODES}
DEEP_MODES = {"deep-lite", "deep", "deep-reasoning"}

DIMENSIONS = [
    {
        "key": "regulation",
        "label": "Regulation",
        "focus": "regulatory actions, government policy, court rulings, export controls, and public-sector contract decisions",
        "category": "news",
    },
    {
        "key": "customers",
        "label": "Customers",
        "focus": "customer wins, losses, renewals, expansions, and adoption announcements",
        "category": "news",
    },
    {
        "key": "competition",
        "label": "Competition",
        "focus": "competitor product launches, pricing moves, market share shifts, and customer displacement",
        "category": "news",
    },
    {
        "key": "supply_chain",
        "label": "Supply Chain",
        "focus": "suppliers, partners, manufacturing capacity, distribution channels, and ecosystem relationships",
        "category": "news",
    },
    {
        "key": "financials",
        "label": "Financials",
        "focus": "earnings results, guidance changes, backlog, remaining performance obligations, and SEC filings",
        "category": None,
    },
    {
        "key": "leadership",
        "label": "Leadership",
        "focus": "executive departures and hires, insider transactions, hiring patterns, and organizational changes",
        "category": "news",
    },
]

SIGNAL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string", "description": "Specific, factual headline of the event"},
                    "summary": {"type": "string", "description": "Two sentences: what happened, with names, figures and dates"},
                    "thesis_impact": {"type": "string", "description": "Why this event strengthens or weakens the thesis"},
                    "direction": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "impact": {"type": "string", "enum": ["high", "medium", "low"]},
                    "event_type": {"type": "string", "description": "Short event label, e.g. Regulatory action, Contract award"},
                    "source_url": {"type": "string", "description": "URL of the single result that reports this event"},
                    "entities": {"type": "string", "description": "Comma-separated companies, agencies or people involved"},
                },
                "required": [
                    "headline", "summary", "thesis_impact", "direction",
                    "impact", "event_type", "source_url", "entities",
                ],
            },
        }
    },
    "required": ["signals"],
}

ECOSYSTEM_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string", "description": "Official company name"},
        "sector": {"type": "string"},
        "competitors": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "customers": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "suppliers": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "partners": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
    },
    "required": ["company_name", "sector", "competitors", "customers", "suppliers", "partners"],
}

DIMENSION_CONCURRENCY = 3


# ── Event bus ────────────────────────────────────────────────────────────────

class RunBus:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        self.done = False
        self.cond = asyncio.Condition()
        self.started = time.monotonic()

    async def emit(self, event: Dict[str, Any]) -> None:
        event = {**event, "seq": len(self.events), "t_ms": int((time.monotonic() - self.started) * 1000)}
        async with self.cond:
            self.events.append(event)
            self.cond.notify_all()

    async def close(self) -> None:
        async with self.cond:
            self.done = True
            self.cond.notify_all()


BUSES: Dict[str, RunBus] = {}
_TASKS: Dict[str, asyncio.Task] = {}


# ── Helpers ──────────────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip().lower())
    host = parsed.netloc.removeprefix("www.")
    return f"{host}{parsed.path.rstrip('/')}"


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.removeprefix("www.")
    except Exception:
        return ""


def _start_date(lookback_days: int) -> str:
    start = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    return start.strftime("%Y-%m-%dT00:00:00.000Z")


def _timestamp(value: Optional[str]) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _cost(data: Dict[str, Any]) -> float:
    cost = data.get("costDollars") or {}
    total = cost.get("total") if isinstance(cost, dict) else None
    return float(total) if isinstance(total, (int, float)) else 0.0


def _summarize_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "domain": domain_of(r.get("url", "")),
            "published_date": r.get("publishedDate"),
        }
        for r in results
    ]


async def exa_search(client: httpx.AsyncClient, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /search with one retry on rate limiting or transient server errors."""
    for attempt in range(2):
        response = await client.post("/search", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code in (429, 500, 502, 503) and attempt == 0:
            await asyncio.sleep(2)
            continue
        try:
            detail = response.json().get("error") or response.text
        except Exception:
            detail = response.text
        raise RuntimeError(f"Exa returned HTTP {response.status_code}: {detail}")
    raise RuntimeError("Exa search failed")


def build_ecosystem_request(company: str, thesis: str) -> Dict[str, Any]:
    return {
        "query": f"{company} company profile: main competitors, major customers, key suppliers and strategic partners",
        "type": "auto",
        "numResults": 8,
        "contents": {"highlights": {"maxCharacters": 400}},
        "outputSchema": ECOSYSTEM_SCHEMA,
        "systemPrompt": (
            f"The user is an equity analyst researching {company}. Their thesis: {thesis}. "
            "Return the official company name, sector, and up to 8 named competitors, customers, "
            "suppliers and partners each. Use only organizations named in the sources."
        ),
    }


def build_dimension_request(
    dimension: Dict[str, Any],
    company_name: str,
    thesis: str,
    mode: str,
    num_results: int,
    lookback_days: int,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "query": f"{company_name} {dimension['focus']}",
        "type": mode,
        "numResults": num_results,
        "startPublishedDate": _start_date(lookback_days),
        "contents": {"highlights": {"maxCharacters": 600}},
        "objective": (
            f"Find specific, recent, verifiable events about {company_name} related to "
            f"{dimension['label'].lower()} that bear on this investment thesis: \"{thesis}\". "
            "Rank primary reporting, filings and official announcements first. "
            "Exclude stock-price commentary, listicles and generic company overviews."
        ),
        "outputSchema": SIGNAL_SCHEMA,
        "systemPrompt": (
            f"You are a buy-side equity analyst covering {company_name}. Thesis: \"{thesis}\". "
            f"From the search results, extract 0 to 4 distinct {dimension['label'].lower()} events that are "
            "material to the thesis. Each signal must come from exactly one result and source_url must be "
            "that result's URL. direction is relative to the thesis (positive = supports it, negative = "
            "challenges it). impact reflects materiality to the thesis. Skip results that are not specific "
            "events. Return an empty list if nothing is material."
        ),
    }
    if dimension.get("category"):
        payload["category"] = dimension["category"]
    if mode in DEEP_MODES:
        payload["additionalQueries"] = [
            f"{company_name} {dimension['label'].lower()} news",
            f"{company_name} {thesis[:200]}",
        ]
    return payload


def extract_signals(dimension: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = data.get("results") or []
    by_url = {normalize_url(r.get("url", "")): r for r in results}
    output = data.get("output") or {}
    content = output.get("content") if isinstance(output, dict) else None
    raw_signals = content.get("signals", []) if isinstance(content, dict) else []
    grounding = output.get("grounding", []) if isinstance(output, dict) else []

    signals: List[Dict[str, Any]] = []
    for index, raw in enumerate(raw_signals):
        if not isinstance(raw, dict) or not raw.get("headline"):
            continue
        prefix = f"signals[{index}]"
        fields = [g for g in grounding if str(g.get("field", "")).startswith(prefix)]

        citations: List[Dict[str, str]] = []
        seen = set()
        for g in fields:
            for c in g.get("citations", []):
                key = normalize_url(c.get("url", ""))
                if key and key not in seen:
                    seen.add(key)
                    citations.append({"url": c.get("url"), "title": c.get("title"), "domain": domain_of(c.get("url", ""))})

        confidences = [g.get("confidence") for g in fields if g.get("confidence")]
        confidence = Counter(confidences).most_common(1)[0][0] if confidences else "low"

        source_url = raw.get("source_url") or ""
        source = by_url.get(normalize_url(source_url))
        if source is None:
            for c in citations:
                source = by_url.get(normalize_url(c["url"]))
                if source:
                    break
        if source is not None:
            source_url = source.get("url", source_url)
        if not source_url and citations:
            source_url = citations[0]["url"]
        if not source_url:
            continue

        direction = raw.get("direction") if raw.get("direction") in ("positive", "negative", "neutral") else "neutral"
        impact = raw.get("impact") if raw.get("impact") in ("high", "medium", "low") else "medium"
        entities = [e.strip() for e in str(raw.get("entities", "")).split(",") if e.strip()]

        signals.append({
            "id": hashlib.sha1(f"{dimension['key']}|{normalize_url(source_url)}|{raw['headline']}".encode()).hexdigest()[:12],
            "dimension": dimension["key"],
            "dimension_label": dimension["label"],
            "headline": raw.get("headline"),
            "summary": raw.get("summary"),
            "thesis_impact": raw.get("thesis_impact"),
            "direction": direction,
            "impact": impact,
            "event_type": raw.get("event_type"),
            "entities": entities[:6],
            "confidence": confidence,
            "source_url": source_url,
            "source_title": (source or {}).get("title"),
            "source_domain": domain_of(source_url),
            "published_date": (source or {}).get("publishedDate"),
            "highlights": (source or {}).get("highlights") or [],
            "citations": citations,
            "grounded_in_results": source is not None,
        })
    return signals


# ── Pipeline ─────────────────────────────────────────────────────────────────

async def _run_ecosystem(client: httpx.AsyncClient, bus: RunBus, company: str, thesis: str) -> Dict[str, Any]:
    payload = build_ecosystem_request(company, thesis)
    await bus.emit({
        "type": "step_start", "step": "ecosystem", "label": "Map company ecosystem",
        "query": payload["query"], "search_type": payload["type"], "request": payload,
    })
    started = time.monotonic()
    data = await exa_search(client, payload)
    results = data.get("results") or []
    content = (data.get("output") or {}).get("content") or {}
    if not isinstance(content, dict):
        content = {}
    ecosystem = {
        "company_name": content.get("company_name") or company,
        "sector": content.get("sector"),
        "competitors": content.get("competitors") or [],
        "customers": content.get("customers") or [],
        "suppliers": content.get("suppliers") or [],
        "partners": content.get("partners") or [],
    }
    await bus.emit({
        "type": "step_sources", "step": "ecosystem", "sources": _summarize_sources(results),
        "request_id": data.get("requestId"), "cost": _cost(data),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
    })
    await bus.emit({"type": "ecosystem", "ecosystem": ecosystem})
    await bus.emit({"type": "step_done", "step": "ecosystem", "summary": f"Resolved {ecosystem['company_name']}"})
    return {"ecosystem": ecosystem, "cost": _cost(data), "sources": results}


async def _run_dimension(
    client: httpx.AsyncClient,
    bus: RunBus,
    semaphore: asyncio.Semaphore,
    dimension: Dict[str, Any],
    run: Dict[str, Any],
    company_name: str,
) -> Dict[str, Any]:
    payload = build_dimension_request(
        dimension, company_name, run["thesis"], run["mode"],
        run["results_per_dimension"], run["lookback_days"],
    )
    async with semaphore:
        await bus.emit({
            "type": "step_start", "step": dimension["key"], "label": dimension["label"],
            "query": payload["query"], "search_type": payload["type"], "request": payload,
        })
        started = time.monotonic()
        try:
            data = await exa_search(client, payload)
        except Exception as exc:
            await bus.emit({"type": "step_error", "step": dimension["key"], "error": str(exc)})
            return {"signals": [], "cost": 0.0, "sources": []}

    results = data.get("results") or []
    await bus.emit({
        "type": "step_sources", "step": dimension["key"], "sources": _summarize_sources(results),
        "request_id": data.get("requestId"), "cost": _cost(data),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
    })
    signals = extract_signals(dimension, data)
    for signal in signals:
        await bus.emit({"type": "signal", "signal": signal})
    await bus.emit({
        "type": "step_done", "step": dimension["key"],
        "summary": f"{len(signals)} signal{'s' if len(signals) != 1 else ''} from {len(results)} sources",
    })
    return {"signals": signals, "cost": _cost(data), "sources": results}


async def execute_run(run_id: str) -> None:
    bus = BUSES[run_id]
    db = SessionLocal()
    run_row = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
    run = {
        "company": run_row.company,
        "thesis": run_row.thesis,
        "mode": run_row.mode,
        "lookback_days": run_row.lookback_days,
        "results_per_dimension": run_row.results_per_dimension,
    }
    run_row.status = "running"
    db.commit()

    all_signals: List[Dict[str, Any]] = []
    ecosystem: Optional[Dict[str, Any]] = None
    total_cost = 0.0
    queries = 0
    source_urls: set = set()
    status = "completed"
    error: Optional[str] = None

    try:
        await bus.emit({
            "type": "run_start", "company": run["company"], "mode": run["mode"],
            "lookback_days": run["lookback_days"],
            "dimensions": [{"key": d["key"], "label": d["label"]} for d in DIMENSIONS],
        })
        async with httpx.AsyncClient(base_url=EXA_BASE_URL, headers=get_exa_headers(), timeout=180.0) as client:
            eco = await _run_ecosystem(client, bus, run["company"], run["thesis"])
            ecosystem = eco["ecosystem"]
            total_cost += eco["cost"]
            queries += 1
            source_urls.update(normalize_url(r.get("url", "")) for r in eco["sources"])

            company_name = ecosystem["company_name"] or run["company"]
            run_row.company_name = company_name
            db.commit()

            semaphore = asyncio.Semaphore(DIMENSION_CONCURRENCY)
            outcomes = await asyncio.gather(*[
                _run_dimension(client, bus, semaphore, d, run, company_name) for d in DIMENSIONS
            ])

        seen_sources: set = set()
        for outcome in outcomes:
            total_cost += outcome["cost"]
            queries += 1
            source_urls.update(normalize_url(r.get("url", "")) for r in outcome["sources"])
            for signal in outcome["signals"]:
                key = normalize_url(signal["source_url"])
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                all_signals.append(signal)
    except Exception as exc:
        logger.exception("Research run %s failed", run_id)
        status = "failed"
        error = str(exc)
        await bus.emit({"type": "run_error", "error": error})

    impact_order = {"high": 0, "medium": 1, "low": 2}
    all_signals.sort(key=lambda s: (impact_order[s["impact"]], -_timestamp(s.get("published_date"))))

    stats = {
        "signals": len(all_signals),
        "high": sum(1 for s in all_signals if s["impact"] == "high"),
        "medium": sum(1 for s in all_signals if s["impact"] == "medium"),
        "low": sum(1 for s in all_signals if s["impact"] == "low"),
        "positive": sum(1 for s in all_signals if s["direction"] == "positive"),
        "negative": sum(1 for s in all_signals if s["direction"] == "negative"),
        "queries": queries,
        "sources_reviewed": len(source_urls - {""}),
        "cost": round(total_cost, 4),
        "elapsed_ms": int((time.monotonic() - bus.started) * 1000),
    }
    await bus.emit({"type": "run_done", "status": status, "stats": stats})

    run_row.status = status
    run_row.error_message = error
    run_row.signals_json = all_signals
    run_row.ecosystem_json = ecosystem
    run_row.stats_json = stats
    run_row.events_json = bus.events
    run_row.completed_at = datetime.utcnow()
    db.commit()
    db.close()

    await bus.close()
    await asyncio.sleep(30)
    BUSES.pop(run_id, None)
    _TASKS.pop(run_id, None)


def start_run(run_id: str) -> None:
    BUSES[run_id] = RunBus()
    _TASKS[run_id] = asyncio.create_task(execute_run(run_id))


# ── Follow-up actions ────────────────────────────────────────────────────────

async def find_people(company_name: str, thesis: str) -> List[Dict[str, Any]]:
    payload = {
        "query": f"{company_name} executives and senior leaders",
        "type": "auto",
        "category": "people",
        "numResults": 8,
        "contents": {"highlights": {"maxCharacters": 300}},
    }
    async with httpx.AsyncClient(base_url=EXA_BASE_URL, headers=get_exa_headers(), timeout=60.0) as client:
        data = await exa_search(client, payload)
    return [
        {
            "name": r.get("title"),
            "url": r.get("url"),
            "domain": domain_of(r.get("url", "")),
            "highlight": (r.get("highlights") or [None])[0],
            "image": r.get("image"),
        }
        for r in data.get("results") or []
    ]


AGENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["supported", "mixed", "challenged"]},
        "summary": {"type": "string", "description": "Three-sentence assessment of the thesis"},
        "bull_points": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "bear_points": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "watch_items": {"type": "array", "items": {"type": "string"}, "maxItems": 5,
                        "description": "Upcoming events or metrics that would change the view"},
    },
    "required": ["verdict", "summary", "bull_points", "bear_points", "watch_items"],
}


def _agent_headers() -> Dict[str, str]:
    from app.core.config import settings
    return {"Authorization": f"Bearer {settings.EXA_API_KEY}", "Content-Type": "application/json"}


async def start_agent(company_name: str, thesis: str, lookback_days: int, effort: str) -> Dict[str, Any]:
    payload = {
        "query": (
            f"Act as a buy-side equity analyst. Evaluate this investment thesis for {company_name}: \"{thesis}\". "
            f"Weigh the strongest evidence for and against it from roughly the last {lookback_days} days, "
            "cite primary sources, and list what upcoming events or metrics would change the view."
        ),
        "effort": effort,
        "outputSchema": AGENT_SCHEMA,
    }
    async with httpx.AsyncClient(base_url=EXA_BASE_URL, headers=_agent_headers(), timeout=60.0) as client:
        response = await client.post("/agent/runs", json=payload)
    if response.status_code not in (200, 201, 202):
        raise RuntimeError(f"Exa Agent returned HTTP {response.status_code}: {response.text[:300]}")
    data = response.json()
    return {"exa_run_id": data.get("id"), "status": data.get("status", "queued"), "effort": effort, "request": payload}


async def poll_agent(exa_run_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=EXA_BASE_URL, headers=_agent_headers(), timeout=60.0) as client:
        response = await client.get(f"/agent/runs/{exa_run_id}")
    if response.status_code != 200:
        raise RuntimeError(f"Exa Agent returned HTTP {response.status_code}: {response.text[:300]}")
    data = response.json()
    output = data.get("output") or {}
    cost = data.get("costDollars") or {}
    return {
        "status": data.get("status"),
        "text": output.get("text"),
        "structured": output.get("structured"),
        "grounding": output.get("grounding"),
        "cost": cost.get("total") if isinstance(cost, dict) else None,
        "error": data.get("error"),
    }
