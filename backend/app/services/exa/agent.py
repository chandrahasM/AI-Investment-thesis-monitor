"""
Exa Agent Service

Manages async Agent runs for deep investigation, enrichment, and validation.

Current Exa Agent API (verified Sep 2026):
- Endpoint: POST https://api.exa.ai/agent/runs
- Auth: Authorization: Bearer {key}
- Effort: minimal ($0.012), low ($0.025), medium ($0.10), high ($0.50),
          xhigh ($1.00), auto (metered, $5 cap), ultra (metered, $20 cap)
- input.data: for row enrichment
- outputSchema: JSON schema (object or text root type)
- Async: poll GET https://api.exa.ai/agent/runs/{id}
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.exa.client import get_exa_client
from app.schemas.agent import AgentRunCreate
from app.models.agent import AgentRun

logger = logging.getLogger(__name__)

AGENT_EFFORT_PRICES = {
    "minimal": 0.012,
    "low": 0.025,
    "medium": 0.10,
    "high": 0.50,
    "xhigh": 1.00,
    "auto": None,   # metered
    "ultra": None,  # metered
}

EFFORT_DESCRIPTIONS = {
    "minimal": "Lowest-cost lookup, very narrow factual tasks",
    "low": "Simple lookups, narrow factual tasks",
    "medium": "Default for most standard research tasks",
    "high": "Harder research, more citations, stricter completeness",
    "xhigh": "High-value tasks where completeness matters most",
    "auto": "Variable-scope work, adapts to task difficulty (metered, up to $5)",
    "ultra": "Exhaustive research, largest list building (metered, up to $20)",
}


def build_agent_request(req: AgentRunCreate) -> Dict[str, Any]:
    """Build Exa Agent API request payload."""
    payload: Dict[str, Any] = {
        "query": req.query,
        "effort": req.effort,
    }

    if req.system_prompt:
        payload["systemPrompt"] = req.system_prompt

    if req.output_schema:
        payload["outputSchema"] = req.output_schema

    if req.input_data:
        payload["input"] = {"data": req.input_data}

    return payload


async def create_agent_run(req: AgentRunCreate, db: Session) -> AgentRun:
    """Start an Exa Agent run and persist it."""
    exa_payload = build_agent_request(req)

    run = AgentRun(
        company_id=req.company_id,
        signal_id=req.signal_id,
        search_result_id=req.search_result_id,
        query=req.query,
        effort=req.effort,
        system_prompt=req.system_prompt,
        input_data_json=req.input_data,
        output_schema_json=req.output_schema,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        async with get_exa_client() as client:
            response = await client.post(
                "/agent/runs",
                json=exa_payload,
                headers={"Authorization": f"Bearer {client.headers.get('x-api-key', '')}"},
            )

        if response.status_code not in (200, 201, 202):
            error_data = response.json() if response.content else {}
            run.status = "failed"
            run.error_message = error_data.get("error", f"HTTP {response.status_code}")
            run.raw_response_json = error_data
            db.commit()
            db.refresh(run)
            return run

        data = response.json()
        run.exa_agent_id = data.get("id")
        run.status = data.get("status", "queued")
        run.raw_response_json = data
        db.commit()
        db.refresh(run)
        return run

    except Exception as e:
        logger.exception("Failed to create Exa Agent run")
        run.status = "failed"
        run.error_message = str(e)
        db.commit()
        db.refresh(run)
        return run


async def poll_agent_run(run_id: int, db: Session) -> AgentRun:
    """Poll Exa for the latest status of an agent run."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run or not run.exa_agent_id:
        return run

    try:
        async with get_exa_client() as client:
            response = await client.get(
                f"/agent/runs/{run.exa_agent_id}",
                headers={"Authorization": f"Bearer {client.headers.get('x-api-key', '')}"},
            )

        if response.status_code != 200:
            return run

        data = response.json()
        run.status = data.get("status", run.status)
        run.raw_response_json = data

        output = data.get("output")
        if output:
            run.output_text = output.get("text")
            run.output_json = output.get("structured")
            run.grounding_json = output.get("grounding")

        cost = data.get("costDollars")
        if cost:
            run.cost_json = cost

        if run.status in ("completed", "failed", "cancelled"):
            run.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(run)
        return run

    except Exception as e:
        logger.exception("Failed to poll Exa Agent run")
        return run


async def wait_for_agent_run(run_id: int, db: Session, max_polls: int = 60, poll_interval: float = 4.0) -> AgentRun:
    """Poll until the run completes or times out."""
    for _ in range(max_polls):
        run = await poll_agent_run(run_id, db)
        if run and run.status in ("completed", "failed", "cancelled"):
            return run
        await asyncio.sleep(poll_interval)
    return db.query(AgentRun).filter(AgentRun.id == run_id).first()
