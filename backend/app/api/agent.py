from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.schemas.agent import AgentRunCreate, AgentRunResponse, EnrichRequest
from app.models.agent import AgentRun
from app.models.search import SearchResult
from app.services.exa.agent import (
    create_agent_run, poll_agent_run, wait_for_agent_run,
    EFFORT_DESCRIPTIONS, AGENT_EFFORT_PRICES, build_agent_request,
)
from app.services.exa.demo_agent import create_demo_agent_run

router = APIRouter(tags=["agent"])

# Pre-built output schemas for common signal types
COMPETITIVE_DISPLACEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "signal_type": {"type": "string"},
        "event_date": {"type": ["string", "null"]},
        "existing_relationship": {"type": ["string", "null"]},
        "competing_product": {"type": ["string", "null"]},
        "workload": {"type": ["string", "null"]},
        "deployment_scale": {"type": ["string", "null"]},
        "replacement_or_complementary": {"type": ["string", "null"]},
        "finding": {"type": "string"},
        "evidence_direction": {"type": "string", "enum": ["supporting", "contradicting", "neutral", "insufficient"]},
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
}

JOB_SIGNAL_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "role": {"type": "string"},
        "job_url": {"type": ["string", "null"]},
        "location": {"type": ["string", "null"]},
        "rocm_required": {"type": ["boolean", "null"]},
        "cuda_required": {"type": ["boolean", "null"]},
        "production_context": {"type": ["string", "null"]},
        "workload": {"type": ["string", "null"]},
        "evidence": {"type": "string"},
        "published_date": {"type": ["string", "null"]},
        "evidence_direction": {"type": "string", "enum": ["supporting", "contradicting", "neutral", "insufficient"]},
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
}

PEOPLE_ENRICHMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "current_role": {"type": ["string", "null"]},
        "current_company": {"type": ["string", "null"]},
        "relevant_previous_roles": {"type": "array", "items": {"type": "string"}},
        "why_relevant": {"type": ["string", "null"]},
        "source_urls": {"type": "array", "items": {"type": "string"}},
        "evidence_direction": {"type": "string", "enum": ["supporting", "contradicting", "neutral", "insufficient"]},
    },
}


def _serialize_run(run: AgentRun) -> AgentRunResponse:
    return AgentRunResponse(
        id=run.id,
        company_id=run.company_id,
        signal_id=run.signal_id,
        search_result_id=run.search_result_id,
        exa_agent_id=run.exa_agent_id,
        query=run.query,
        effort=run.effort,
        system_prompt=run.system_prompt,
        input_data_json=run.input_data_json,
        output_schema_json=run.output_schema_json,
        output_json=run.output_json,
        output_text=run.output_text,
        grounding_json=run.grounding_json,
        status=run.status,
        cost_json=run.cost_json,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
        is_demo=bool(run.raw_response_json and run.raw_response_json.get("_demo")),
    )


@router.get("/api/agent/config")
def agent_config():
    """Return agent configuration metadata for UI."""
    return {
        "effort_options": [
            {"value": "minimal", "label": "Minimal", "description": EFFORT_DESCRIPTIONS["minimal"], "price": "$0.012 / request"},
            {"value": "low", "label": "Low", "description": EFFORT_DESCRIPTIONS["low"], "price": "$0.025 / request"},
            {"value": "medium", "label": "Medium", "description": EFFORT_DESCRIPTIONS["medium"], "price": "$0.10 / request", "default": True},
            {"value": "high", "label": "High", "description": EFFORT_DESCRIPTIONS["high"], "price": "$0.50 / request"},
            {"value": "xhigh", "label": "XHigh", "description": EFFORT_DESCRIPTIONS["xhigh"], "price": "$1.00 / request"},
            {"value": "auto", "label": "Auto", "description": EFFORT_DESCRIPTIONS["auto"], "price": "Metered (up to $5)"},
            {"value": "ultra", "label": "Ultra", "description": EFFORT_DESCRIPTIONS["ultra"], "price": "Metered (up to $20)"},
        ],
        "preset_schemas": {
            "competitive_displacement": COMPETITIVE_DISPLACEMENT_SCHEMA,
            "job_signal": JOB_SIGNAL_SCHEMA,
            "people_enrichment": PEOPLE_ENRICHMENT_SCHEMA,
        },
        "is_demo": settings.is_demo_mode,
    }


@router.post("/api/agent-runs", response_model=AgentRunResponse)
async def create_run(req: AgentRunCreate, db: Session = Depends(get_db)):
    """Start an Exa Agent run. Returns immediately with queued/pending status."""
    if settings.is_demo_mode:
        run = await create_demo_agent_run(req, db)
    else:
        run = await create_agent_run(req, db)
    return _serialize_run(run)


@router.get("/api/agent-runs/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get current status of an agent run. Poll this until status is completed/failed."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    # If still running and not demo, poll Exa for latest status
    if run.status in ("pending", "queued", "running") and run.exa_agent_id and not settings.is_demo_mode:
        run = await poll_agent_run(run_id, db)

    return _serialize_run(run)


@router.post("/api/agent-runs/{run_id}/wait", response_model=AgentRunResponse)
async def wait_for_run(run_id: int, db: Session = Depends(get_db)):
    """Block until the agent run completes (up to ~4 minutes)."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    if run.status in ("completed", "failed", "cancelled"):
        return _serialize_run(run)

    if settings.is_demo_mode:
        return _serialize_run(run)

    run = await wait_for_agent_run(run_id, db)
    return _serialize_run(run)


@router.post("/api/search-results/{result_id}/enrich", response_model=AgentRunResponse)
async def enrich_result(result_id: int, req: EnrichRequest, db: Session = Depends(get_db)):
    """
    Enrich a search result using Exa Agent with input.data.
    Passes the search result as input data to the Agent.
    """
    result = db.query(SearchResult).filter(SearchResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Search result not found")

    # Build enrichment query from the result
    query = (
        f"Research this candidate and determine its relevance as an investment signal. "
        f"Investigate: {result.title or result.url}. "
        f"Determine: existing technology relationships, deployment context (production vs. pilot), "
        f"whether this represents replacement or complementary adoption, evidence quality, "
        f"and what remains unknown."
    )

    # Pass search result as input.data
    input_data = [{
        "title": result.title,
        "url": result.url,
        "domain": result.domain,
        "published_date": result.published_date,
        "excerpt": (result.highlights_json or [""])[0] if result.highlights_json else result.summary or "",
        "signal": "investment signal research",
    }]

    # Choose schema based on signal type if available
    from app.models.signal import Signal
    schema = COMPETITIVE_DISPLACEMENT_SCHEMA
    if result.search_run and result.search_run.signal:
        sig_type = result.search_run.signal.signal_type
        if sig_type == "job_activity":
            schema = JOB_SIGNAL_SCHEMA
        elif sig_type == "people_change":
            schema = PEOPLE_ENRICHMENT_SCHEMA

    agent_req = AgentRunCreate(
        query=query,
        effort=req.effort,
        output_schema=schema,
        input_data=input_data,
        company_id=req.company_id,
        signal_id=req.signal_id,
        search_result_id=result_id,
    )

    if settings.is_demo_mode:
        run = await create_demo_agent_run(agent_req, db)
    else:
        run = await create_agent_run(agent_req, db)
        # For enrichment, wait for completion (it's user-initiated)
        if run.status in ("pending", "queued") and run.exa_agent_id:
            run = await wait_for_agent_run(run.id, db, max_polls=30, poll_interval=4.0)

    return _serialize_run(run)
