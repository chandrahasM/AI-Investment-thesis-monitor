"""
Exa Search Service

Maps application SearchRequest → Exa API request,
calls Exa, normalizes results, captures metadata.

Current Exa Search API (verified Sep 2026):
- Endpoint: POST https://api.exa.ai/search
- Auth: x-api-key header
- Types: instant, fast, auto, deep-lite, deep, deep-reasoning
- Category restriction: 'company' and 'people' categories do NOT support
  startPublishedDate, endPublishedDate, or excludeDomains

NOTE: snapshotAsOf is NOT a current API parameter. UI shows graceful message.
"""

import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.exa.client import get_exa_client
from app.services.exa.normalization import normalize_search_result, normalize_cost
from app.schemas.search import SearchRequest
from app.models.search import SearchRun, SearchResult
import logging

logger = logging.getLogger(__name__)

# Categories that have restricted parameter support
RESTRICTED_CATEGORIES = {"company", "people"}


def build_exa_request(req: SearchRequest) -> Dict[str, Any]:
    """
    Build the Exa Search API request payload from our SearchRequest.
    Respects category-specific parameter restrictions.
    """
    payload: Dict[str, Any] = {
        "query": req.query,
        "type": req.search_type,
        "numResults": req.num_results,
    }

    is_restricted_category = req.category in RESTRICTED_CATEGORIES

    # Date filters — not supported for company/people categories
    if not is_restricted_category:
        if req.start_published_date:
            payload["startPublishedDate"] = req.start_published_date
        if req.end_published_date:
            payload["endPublishedDate"] = req.end_published_date

    # Domain filters
    if req.include_domains:
        payload["includeDomains"] = req.include_domains

    # excludeDomains not supported for company/people categories
    if req.exclude_domains and not is_restricted_category:
        payload["excludeDomains"] = req.exclude_domains

    # Category
    if req.category:
        payload["category"] = req.category

    # Objective and systemPrompt
    if req.objective:
        payload["objective"] = req.objective
    if req.system_prompt:
        payload["systemPrompt"] = req.system_prompt

    # Content options
    contents: Dict[str, Any] = {}
    if req.content_options.highlights:
        contents["highlights"] = True
    if req.content_options.text:
        contents["text"] = True
    if req.content_options.summary:
        contents["summary"] = True

    if contents:
        payload["contents"] = contents

    return payload


async def run_search(
    req: SearchRequest,
    db: Session,
) -> SearchRun:
    """Execute an Exa search and persist results."""
    exa_payload = build_exa_request(req)

    # Create search run record
    run = SearchRun(
        company_id=req.company_id,
        signal_id=req.signal_id,
        query=req.query,
        request_json=exa_payload,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    start_ms = time.time() * 1000

    try:
        async with get_exa_client() as client:
            response = await client.post("/search", json=exa_payload)

        elapsed_ms = time.time() * 1000 - start_ms

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", f"HTTP {response.status_code}")
            run.status = "failed"
            run.error_message = error_msg
            run.response_json = error_data
            db.commit()
            db.refresh(run)
            return run

        data = response.json()
        run.status = "completed"
        run.exa_request_id = data.get("requestId")
        run.search_time_ms = data.get("searchTime") or elapsed_ms
        run.cost_json = normalize_cost(data.get("costDollars"))
        run.response_json = {
            "requestId": data.get("requestId"),
            "searchTime": data.get("searchTime"),
            "resolvedSearchType": data.get("resolvedSearchType"),
            "costDollars": data.get("costDollars"),
            "result_count": len(data.get("results", [])),
        }
        db.commit()

        # Persist individual results
        for raw_result in data.get("results", []):
            normalized = normalize_search_result(raw_result, run.id)
            result = SearchResult(**normalized)
            db.add(result)

        db.commit()
        db.refresh(run)
        return run

    except Exception as e:
        logger.exception("Exa search failed")
        run.status = "failed"
        run.error_message = str(e)
        db.commit()
        db.refresh(run)
        return run
