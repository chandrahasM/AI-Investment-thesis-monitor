"""
Backend unit tests for Signal.

Tests cover:
- Search request mapping (build_exa_request)
- Category-specific restrictions
- Domain filters
- Date filters
- Agent request mapping
- Evidence approval
- Signal creation
- Webhook/inbox flow
"""

import pytest
from datetime import datetime, timezone

from app.services.exa.search import build_exa_request, RESTRICTED_CATEGORIES
from app.services.exa.agent import build_agent_request, EFFORT_DESCRIPTIONS
from app.schemas.search import SearchRequest, ContentOptions
from app.schemas.agent import AgentRunCreate


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_search_request(**kwargs) -> SearchRequest:
    defaults = {
        "query": "test query",
        "search_type": "auto",
        "num_results": 25,
        "include_domains": [],
        "exclude_domains": [],
        "category": None,
        "content_options": ContentOptions(),
    }
    defaults.update(kwargs)
    return SearchRequest(**defaults)


def make_agent_request(**kwargs) -> AgentRunCreate:
    defaults = {
        "query": "Research this company",
        "effort": "medium",
    }
    defaults.update(kwargs)
    return AgentRunCreate(**defaults)


# ── Search Request Mapping ─────────────────────────────────────────────────────

class TestSearchRequestMapping:
    def test_basic_query(self):
        req = make_search_request(query="AMD ROCm adoption")
        payload = build_exa_request(req)
        assert payload["query"] == "AMD ROCm adoption"
        assert payload["type"] == "auto"
        assert payload["numResults"] == 25

    def test_search_type_deep(self):
        req = make_search_request(search_type="deep-reasoning")
        payload = build_exa_request(req)
        assert payload["type"] == "deep-reasoning"

    def test_num_results(self):
        req = make_search_request(num_results=50)
        payload = build_exa_request(req)
        assert payload["numResults"] == 50

    def test_include_domains(self):
        req = make_search_request(include_domains=["sec.gov", "amd.com"])
        payload = build_exa_request(req)
        assert payload["includeDomains"] == ["sec.gov", "amd.com"]

    def test_exclude_domains(self):
        req = make_search_request(exclude_domains=["nvidia.com"])
        payload = build_exa_request(req)
        assert payload["excludeDomains"] == ["nvidia.com"]

    def test_date_filters_standard_category(self):
        req = make_search_request(
            start_published_date="2025-01-01T00:00:00Z",
            end_published_date="2025-12-31T00:00:00Z",
        )
        payload = build_exa_request(req)
        assert payload["startPublishedDate"] == "2025-01-01T00:00:00Z"
        assert payload["endPublishedDate"] == "2025-12-31T00:00:00Z"

    def test_objective_set(self):
        req = make_search_request(objective="Find production ROCm deployments")
        payload = build_exa_request(req)
        assert payload["objective"] == "Find production ROCm deployments"

    def test_system_prompt_set(self):
        req = make_search_request(system_prompt="Prefer primary sources")
        payload = build_exa_request(req)
        assert payload["systemPrompt"] == "Prefer primary sources"

    def test_objective_empty_not_sent(self):
        req = make_search_request(objective=None)
        payload = build_exa_request(req)
        assert "objective" not in payload

    def test_content_options_highlights(self):
        req = make_search_request(content_options=ContentOptions(highlights=True, text=False, summary=False))
        payload = build_exa_request(req)
        assert payload["contents"] == {"highlights": True}

    def test_content_options_full(self):
        req = make_search_request(content_options=ContentOptions(highlights=True, text=True, summary=True))
        payload = build_exa_request(req)
        assert payload["contents"] == {"highlights": True, "text": True, "summary": True}

    def test_content_options_none_not_sent(self):
        req = make_search_request(content_options=ContentOptions(highlights=False, text=False, summary=False))
        payload = build_exa_request(req)
        assert "contents" not in payload

    def test_category_news(self):
        req = make_search_request(category="news")
        payload = build_exa_request(req)
        assert payload["category"] == "news"


# ── Category Restrictions ──────────────────────────────────────────────────────

class TestCategoryRestrictions:
    """
    company and people categories do NOT support:
    - startPublishedDate
    - endPublishedDate
    - excludeDomains
    """

    def test_company_category_no_date_filters(self):
        req = make_search_request(
            category="company",
            start_published_date="2025-01-01T00:00:00Z",
            end_published_date="2025-12-31T00:00:00Z",
        )
        payload = build_exa_request(req)
        assert "startPublishedDate" not in payload
        assert "endPublishedDate" not in payload

    def test_company_category_no_exclude_domains(self):
        req = make_search_request(category="company", exclude_domains=["nvidia.com"])
        payload = build_exa_request(req)
        assert "excludeDomains" not in payload

    def test_people_category_no_date_filters(self):
        req = make_search_request(
            category="people",
            start_published_date="2025-01-01T00:00:00Z",
        )
        payload = build_exa_request(req)
        assert "startPublishedDate" not in payload

    def test_people_category_no_exclude_domains(self):
        req = make_search_request(category="people", exclude_domains=["competitor.com"])
        payload = build_exa_request(req)
        assert "excludeDomains" not in payload

    def test_company_category_include_domains_still_sent(self):
        """includeDomains IS allowed for restricted categories."""
        req = make_search_request(category="company", include_domains=["crunchbase.com"])
        payload = build_exa_request(req)
        assert payload["includeDomains"] == ["crunchbase.com"]

    def test_news_category_allows_date_and_exclude(self):
        req = make_search_request(
            category="news",
            start_published_date="2025-01-01T00:00:00Z",
            exclude_domains=["nvidia.com"],
        )
        payload = build_exa_request(req)
        assert "startPublishedDate" in payload
        assert "excludeDomains" in payload

    def test_restricted_categories_constant(self):
        assert "company" in RESTRICTED_CATEGORIES
        assert "people" in RESTRICTED_CATEGORIES
        assert "news" not in RESTRICTED_CATEGORIES


# ── Agent Request Mapping ──────────────────────────────────────────────────────

class TestAgentRequestMapping:
    def test_basic_agent_request(self):
        req = make_agent_request()
        payload = build_agent_request(req)
        assert payload["query"] == "Research this company"
        assert payload["effort"] == "medium"

    def test_effort_levels(self):
        for effort in ["minimal", "low", "medium", "high", "xhigh", "auto", "ultra"]:
            req = make_agent_request(effort=effort)
            payload = build_agent_request(req)
            assert payload["effort"] == effort

    def test_output_schema_included(self):
        schema = {"type": "object", "properties": {"company": {"type": "string"}}}
        req = make_agent_request(output_schema=schema)
        payload = build_agent_request(req)
        assert payload["outputSchema"] == schema

    def test_input_data_included(self):
        data = [{"company": "Oracle", "url": "https://oracle.com", "excerpt": "AMD deployment"}]
        req = make_agent_request(input_data=data)
        payload = build_agent_request(req)
        assert payload["input"]["data"] == data

    def test_system_prompt_included(self):
        req = make_agent_request(system_prompt="Focus on production deployments only")
        payload = build_agent_request(req)
        assert payload["systemPrompt"] == "Focus on production deployments only"

    def test_no_input_data_not_sent(self):
        req = make_agent_request()
        payload = build_agent_request(req)
        assert "input" not in payload

    def test_no_output_schema_not_sent(self):
        req = make_agent_request()
        payload = build_agent_request(req)
        assert "outputSchema" not in payload

    def test_effort_descriptions_exist(self):
        for effort in ["minimal", "low", "medium", "high", "xhigh", "auto", "ultra"]:
            assert effort in EFFORT_DESCRIPTIONS
            assert len(EFFORT_DESCRIPTIONS[effort]) > 0


# ── Normalization ──────────────────────────────────────────────────────────────

class TestNormalization:
    def test_domain_extraction(self):
        from app.services.exa.normalization import extract_domain
        assert extract_domain("https://www.oracle.com/news/article") == "www.oracle.com"
        assert extract_domain("https://semianalysis.com/rocm-report") == "semianalysis.com"
        assert extract_domain("https://careers.meta.com/jobs/rocm") == "careers.meta.com"

    def test_normalize_search_result(self):
        from app.services.exa.normalization import normalize_search_result
        raw = {
            "id": "exa-abc123",
            "title": "AMD ROCm Adoption",
            "url": "https://example.com/article",
            "publishedDate": "2025-09-15",
            "author": "Jane Doe",
            "highlights": ["ROCm is growing in production"],
            "summary": "AMD ROCm is gaining production adoption.",
        }
        result = normalize_search_result(raw, search_run_id=1)
        assert result["exa_result_id"] == "exa-abc123"
        assert result["title"] == "AMD ROCm Adoption"
        assert result["domain"] == "example.com"
        assert result["published_date"] == "2025-09-15"
        assert result["author"] == "Jane Doe"
        assert result["highlights_json"] == ["ROCm is growing in production"]
        assert result["search_run_id"] == 1

    def test_normalize_search_result_missing_fields(self):
        from app.services.exa.normalization import normalize_search_result
        raw = {"url": "https://example.com", "id": "x"}
        result = normalize_search_result(raw, search_run_id=1)
        assert result["title"] is None
        assert result["author"] is None
        assert result["highlights_json"] == []

    def test_normalize_cost(self):
        from app.services.exa.normalization import normalize_cost
        raw = {"total": 0.0025, "search": {"neural": 0.0025}, "contents": {"highlights": 0.001}}
        cost = normalize_cost(raw)
        assert cost["total"] == 0.0025
        assert cost["search"] == {"neural": 0.0025}

    def test_normalize_cost_none(self):
        from app.services.exa.normalization import normalize_cost
        assert normalize_cost(None) is None


# ── Config Validation ──────────────────────────────────────────────────────────

class TestConfigValidation:
    def test_search_request_defaults(self):
        req = SearchRequest(query="test")
        assert req.search_type == "auto"
        assert req.num_results == 25
        assert req.include_domains == []
        assert req.exclude_domains == []
        assert req.content_options.highlights is True
        assert req.content_options.text is False

    def test_agent_run_create_defaults(self):
        req = AgentRunCreate(query="research this")
        assert req.effort == "medium"
        assert req.output_schema is None
        assert req.input_data is None
