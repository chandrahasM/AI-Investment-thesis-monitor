from app.services.research.pipeline import (
    DIMENSIONS,
    SIGNAL_SCHEMA,
    build_dimension_request,
    extract_signals,
    normalize_url,
)

REGULATION = next(d for d in DIMENSIONS if d["key"] == "regulation")
FINANCIALS = next(d for d in DIMENSIONS if d["key"] == "financials")


def _count_properties(schema):
    total = 0
    for prop in schema.get("properties", {}).values():
        total += 1
        if prop.get("type") == "object":
            total += _count_properties(prop)
        if prop.get("type") == "array" and prop["items"].get("type") == "object":
            total += _count_properties(prop["items"])
    return total


def test_signal_schema_within_exa_limits():
    assert _count_properties(SIGNAL_SCHEMA) <= 10
    assert SIGNAL_SCHEMA["properties"]["signals"]["items"]


def test_dimension_request_uses_mode_dates_and_schema():
    payload = build_dimension_request(REGULATION, "Palantir", "Switching costs are high", "fast", 8, 30)
    assert payload["type"] == "fast"
    assert payload["numResults"] == 8
    assert payload["category"] == "news"
    assert payload["startPublishedDate"].endswith("T00:00:00.000Z")
    assert payload["outputSchema"] is SIGNAL_SCHEMA
    assert "additionalQueries" not in payload


def test_deep_modes_add_query_variations():
    payload = build_dimension_request(FINANCIALS, "Palantir", "Switching costs are high", "deep", 8, 30)
    assert len(payload["additionalQueries"]) == 2
    assert "category" not in payload


def test_normalize_url_ignores_scheme_www_and_trailing_slash():
    assert normalize_url("https://www.Example.com/a/") == normalize_url("http://example.com/a")


def test_extract_signals_matches_source_and_grounding():
    data = {
        "results": [
            {"url": "https://www.defenseone.com/story/", "title": "Story", "publishedDate": "2026-08-01T00:00:00.000Z",
             "highlights": ["Pentagon funds Palantir"]},
        ],
        "output": {
            "content": {"signals": [{
                "headline": "Pentagon funds Palantir", "summary": "s", "thesis_impact": "t",
                "direction": "positive", "impact": "high", "event_type": "Contract",
                "source_url": "https://defenseone.com/story", "entities": "Palantir, DoD",
            }]},
            "grounding": [
                {"field": "signals[0].headline", "confidence": "high",
                 "citations": [{"url": "https://www.defenseone.com/story/", "title": "Story"}]},
                {"field": "signals[0].impact", "confidence": "medium", "citations": []},
                {"field": "signals[0].direction", "confidence": "high", "citations": []},
            ],
        },
    }
    [signal] = extract_signals(REGULATION, data)
    assert signal["grounded_in_results"] is True
    assert signal["published_date"] == "2026-08-01T00:00:00.000Z"
    assert signal["highlights"] == ["Pentagon funds Palantir"]
    assert signal["confidence"] == "high"
    assert signal["entities"] == ["Palantir", "DoD"]
    assert signal["source_domain"] == "defenseone.com"


def test_extract_signals_coerces_invalid_enums_and_skips_empty():
    data = {
        "results": [],
        "output": {
            "content": {"signals": [
                {"headline": "", "source_url": "https://x.com"},
                {"headline": "H", "direction": "bullish", "impact": "huge", "source_url": "https://x.com/a", "entities": ""},
            ]},
            "grounding": [],
        },
    }
    [signal] = extract_signals(REGULATION, data)
    assert signal["direction"] == "neutral"
    assert signal["impact"] == "medium"
    assert signal["confidence"] == "low"
    assert signal["grounded_in_results"] is False
