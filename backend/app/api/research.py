import asyncio
import json
import secrets
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.models.research import ResearchRun
from app.services.research import pipeline

router = APIRouter(prefix="/api/research", tags=["research"])


class ResearchRunCreate(BaseModel):
    company: str = Field(min_length=1, max_length=100)
    thesis: str = Field(min_length=10, max_length=2000)
    mode: str = "auto"
    lookback_days: int = Field(default=90, ge=1, le=730)
    results_per_dimension: int = Field(default=8, ge=3, le=25)


class AgentStart(BaseModel):
    effort: Literal["minimal", "low", "medium", "high"] = "low"


def _summary(run: ResearchRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "company": run.company,
        "company_name": run.company_name,
        "thesis": run.thesis,
        "mode": run.mode,
        "lookback_days": run.lookback_days,
        "results_per_dimension": run.results_per_dimension,
        "status": run.status,
        "stats": run.stats_json,
        "created_at": run.created_at.isoformat() + "Z" if run.created_at else None,
    }


def _detail(run: ResearchRun) -> Dict[str, Any]:
    return {
        **_summary(run),
        "error_message": run.error_message,
        "signals": run.signals_json or [],
        "ecosystem": run.ecosystem_json,
        "people": run.people_json,
        "agent": run.agent_json,
    }


def _get_run(db: Session, run_id: str) -> ResearchRun:
    run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.get("/config")
def get_config():
    return {
        "exa_available": settings.exa_available,
        "modes": pipeline.SEARCH_MODES,
        "dimensions": [{"key": d["key"], "label": d["label"], "focus": d["focus"]} for d in pipeline.DIMENSIONS],
    }


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    runs = db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(50).all()
    return [_summary(r) for r in runs]


@router.post("/runs")
async def create_run(payload: ResearchRunCreate, db: Session = Depends(get_db)):
    if not settings.exa_available:
        raise HTTPException(status_code=400, detail="EXA_API_KEY is not configured on the server.")
    if payload.mode not in pipeline.VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Unknown search mode '{payload.mode}'")

    run = ResearchRun(
        id=f"th_{secrets.token_hex(5)}",
        company=payload.company.strip(),
        thesis=payload.thesis.strip(),
        mode=payload.mode,
        lookback_days=payload.lookback_days,
        results_per_dimension=payload.results_per_dimension,
        status="pending",
        events_json=[],
        signals_json=[],
    )
    db.add(run)
    db.commit()
    pipeline.start_run(run.id)
    return _summary(run)


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    return _detail(_get_run(db, run_id))


@router.delete("/runs/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)):
    run = _get_run(db, run_id)
    if run.status in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Cannot delete a run that is still in progress")
    db.delete(run)
    db.commit()
    return {"deleted": run_id}


def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str):
    """Replay every event of a run, then tail new events until the run finishes."""

    async def generate():
        bus = pipeline.BUSES.get(run_id)
        if bus is None:
            db = SessionLocal()
            try:
                run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
                events = list(run.events_json or []) if run else []
            finally:
                db.close()
            for event in events:
                yield _sse(event)
            yield _sse({"type": "stream_end"})
            return

        index = 0
        while True:
            try:
                async with bus.cond:
                    await asyncio.wait_for(
                        bus.cond.wait_for(lambda: len(bus.events) > index or bus.done),
                        timeout=15,
                    )
                    batch = bus.events[index:]
                    index = len(bus.events)
                    finished = bus.done
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            for event in batch:
                yield _sse(event)
            if finished and index == len(bus.events):
                yield _sse({"type": "stream_end"})
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/runs/{run_id}/people")
async def find_people(run_id: str, db: Session = Depends(get_db)):
    run = _get_run(db, run_id)
    try:
        people = await pipeline.find_people(run.company_name or run.company, run.thesis)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    run.people_json = people
    db.commit()
    return people


@router.post("/runs/{run_id}/agent")
async def start_agent(run_id: str, payload: AgentStart, db: Session = Depends(get_db)):
    run = _get_run(db, run_id)
    try:
        agent = await pipeline.start_agent(run.company_name or run.company, run.thesis, run.lookback_days, payload.effort)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    run.agent_json = agent
    db.commit()
    return agent


@router.get("/runs/{run_id}/agent")
async def poll_agent(run_id: str, db: Session = Depends(get_db)):
    run = _get_run(db, run_id)
    agent: Optional[Dict[str, Any]] = run.agent_json
    if not agent or not agent.get("exa_run_id"):
        raise HTTPException(status_code=404, detail="No agent run for this research run")
    if agent.get("status") in ("completed", "failed", "cancelled"):
        return agent
    try:
        update = await pipeline.poll_agent(agent["exa_run_id"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    run.agent_json = {**agent, **update}
    db.commit()
    return run.agent_json
