from urllib.parse import urlparse
from typing import Any, Dict, List, Optional


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url


def normalize_search_result(raw: Dict[str, Any], search_run_id: int) -> Dict[str, Any]:
    """Normalize a raw Exa search result into our internal format."""
    highlights = raw.get("highlights", []) or []
    entities = raw.get("entities", []) or []

    return {
        "search_run_id": search_run_id,
        "exa_result_id": raw.get("id"),
        "title": raw.get("title"),
        "url": raw.get("url", ""),
        "domain": extract_domain(raw.get("url", "")),
        "published_date": raw.get("publishedDate"),
        "author": raw.get("author"),
        "highlights_json": highlights,
        "summary": raw.get("summary"),
        "text": raw.get("text"),
        "entities_json": entities,
        "raw_metadata_json": {
            "image": raw.get("image"),
            "favicon": raw.get("favicon"),
            "highlight_scores": raw.get("highlightScores"),
            "subpages": raw.get("subpages"),
        },
    }


def normalize_cost(cost_raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Normalize Exa cost response."""
    if not cost_raw:
        return None
    return {
        "total": cost_raw.get("total"),
        "search": cost_raw.get("search"),
        "contents": cost_raw.get("contents"),
        "summary": cost_raw.get("summary"),
    }
