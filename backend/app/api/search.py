from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.schemas.search import SearchRequest, SearchRunResponse, SearchResultResponse
from app.models.search import SearchRun, SearchResult
from app.services.exa.search import run_search, build_exa_request
from app.services.exa.demo_search import run_demo_search

router = APIRouter(tags=["search"])

# Notify frontend about snapshot unavailability
SNAPSHOT_NOTE = (
    "Point-in-time / snapshotAsOf is not available in the current Exa Search API. "
    "Search results reflect the current index."
)


def _serialize_run(run: SearchRun, db: Session, include_results: bool = False) -> SearchRunResponse:
    resp = SearchRunResponse(
        id=run.id,
        company_id=run.company_id,
        signal_id=run.signal_id,
        query=run.query,
        request_json=run.request_json,
        exa_request_id=run.exa_request_id,
        search_time_ms=run.search_time_ms,
        cost_json=run.cost_json,
        status=run.status,
        error_message=run.error_message,
        created_at=run.created_at,
        is_demo=bool(run.request_json and run.request_json.get("_demo")),
    )
    if include_results:
        results = db.query(SearchResult).filter(SearchResult.search_run_id == run.id).all()
        resp.results = [_serialize_result(r) for r in results]
        resp.result_count = len(resp.results)
    else:
        resp.result_count = db.query(SearchResult).filter(SearchResult.search_run_id == run.id).count()
    return resp


def _serialize_result(r: SearchResult) -> SearchResultResponse:
    return SearchResultResponse(
        id=r.id,
        search_run_id=r.search_run_id,
        exa_result_id=r.exa_result_id,
        title=r.title,
        url=r.url,
        domain=r.domain,
        published_date=r.published_date,
        author=r.author,
        highlights=r.highlights_json or [],
        summary=r.summary,
        text=r.text,
        entities=r.entities_json or [],
        raw_metadata=r.raw_metadata_json,
    )


@router.post("/api/search", response_model=SearchRunResponse)
async def search(req: SearchRequest, db: Session = Depends(get_db)):
    """
    Execute an Exa search. Returns a search run with normalized results.
    NOTE: snapshotAsOf is not supported in the current Exa API.
    Category restrictions: 'company' and 'people' categories do not support
    date filters or excludeDomains.
    """
    if settings.is_demo_mode:
        run = await run_demo_search(req, db)
    else:
        run = await run_search(req, db)

    return _serialize_run(run, db, include_results=True)


@router.get("/api/search/config-info")
def search_config_info():
    """Return search configuration metadata for UI."""
    return {
        "search_types": [
            {"value": "auto", "label": "Auto", "description": "Balanced quality and speed. Recommended for most tasks.", "default": True},
            {"value": "instant", "label": "Instant", "description": "Minimum latency — real-time experiences, voice agents, autocomplete."},
            {"value": "fast", "label": "Fast", "description": "High-quality with reduced latency — user-facing search and interactive workflows."},
            {"value": "deep-lite", "label": "Deep Lite", "description": "Lightweight research with synthesized results (~4s latency)."},
            {"value": "deep", "label": "Deep", "description": "Multi-step research with synthesis — comprehensive but slower."},
            {"value": "deep-reasoning", "label": "Deep Reasoning", "description": "Adds stronger reasoning — best for complex analysis and decision-making."},
        ],
        "categories": [
            {"value": None, "label": "All"},
            {"value": "news", "label": "News"},
            {"value": "company", "label": "Company", "restricted": True, "restriction_note": "Date filters and excludeDomains not supported"},
            {"value": "people", "label": "People", "restricted": True, "restriction_note": "Date filters and excludeDomains not supported"},
            {"value": "financial report", "label": "Financial Report"},
            {"value": "publication", "label": "Publication"},
            {"value": "personal site", "label": "Personal Site"},
        ],
        "snapshot_supported": False,
        "snapshot_note": SNAPSHOT_NOTE,
        "max_results": 100,
        "is_demo": settings.is_demo_mode,
    }


@router.get("/api/search-runs/{run_id}", response_model=SearchRunResponse)
def get_search_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Search run not found")
    return _serialize_run(run, db, include_results=True)


@router.get("/api/search-runs/{run_id}/results", response_model=List[SearchResultResponse])
def get_search_run_results(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Search run not found")
    results = db.query(SearchResult).filter(SearchResult.search_run_id == run_id).all()
    return [_serialize_result(r) for r in results]


@router.get("/api/search-results/{result_id}", response_model=SearchResultResponse)
def get_search_result(result_id: int, db: Session = Depends(get_db)):
    result = db.query(SearchResult).filter(SearchResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Search result not found")
    return _serialize_result(result)
