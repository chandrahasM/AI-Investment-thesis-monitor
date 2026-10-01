"""
Demo Search Service — returns deterministic fixture data for NVDA demo.
Used when DEMO_MODE=true or EXA_API_KEY is not set.
Never mixed with real Exa responses.
"""

import time
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.search import SearchRequest
from app.models.search import SearchRun, SearchResult


DEMO_ROCM_RESULTS = [
    {
        "exa_result_id": "demo-r001",
        "title": "Meta AI Infrastructure Team Hiring AMD ROCm Engineers",
        "url": "https://careers.meta.com/jobs/rocm-infrastructure-2025",
        "domain": "careers.meta.com",
        "published_date": "2025-09-15",
        "author": None,
        "highlights_json": [
            "We are seeking engineers with production experience deploying AMD ROCm on large-scale inference clusters.",
            "Experience with ROCm stack in production environments required; CUDA experience a plus.",
        ],
        "summary": "Meta is hiring AI infrastructure engineers with production AMD ROCm experience for large-scale inference.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Meta Platforms"}}],
        "raw_metadata_json": {"favicon": None},
    },
    {
        "exa_result_id": "demo-r002",
        "title": "Databricks Opens Roles for ROCm Compute Platform Engineers",
        "url": "https://www.databricks.com/company/careers/rocm-platform",
        "domain": "databricks.com",
        "published_date": "2025-10-02",
        "author": None,
        "highlights_json": [
            "Join our compute platform team to build next-generation ML infrastructure on AMD ROCm.",
            "We expect production ROCm workloads to grow significantly in 2026.",
        ],
        "summary": "Databricks is expanding its ROCm compute platform team for production ML workloads.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Databricks"}}],
        "raw_metadata_json": {},
    },
    {
        "exa_result_id": "demo-r003",
        "title": "Microsoft Azure Adds ROCm-Optimized VM Series",
        "url": "https://azure.microsoft.com/en-us/blog/rocm-vms-2025/",
        "domain": "azure.microsoft.com",
        "published_date": "2025-08-20",
        "author": "Azure Infrastructure Team",
        "highlights_json": [
            "Azure is launching HBv5 instances with ROCm support for production AI training and inference.",
            "Multiple enterprise customers have requested ROCm-native infrastructure for cost optimization.",
        ],
        "summary": "Microsoft Azure announces new VM series with ROCm optimization for production AI workloads.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Microsoft"}}],
        "raw_metadata_json": {},
    },
    {
        "exa_result_id": "demo-r004",
        "title": "Job: Senior GPU Software Engineer - ROCm Production Systems at Snowflake",
        "url": "https://careers.snowflake.com/jobs/senior-gpu-rocm",
        "domain": "careers.snowflake.com",
        "published_date": "2025-09-28",
        "author": None,
        "highlights_json": [
            "5+ years experience with ROCm or CUDA in production distributed training environments.",
            "Will lead migration of select inference workloads to AMD MI300X infrastructure.",
        ],
        "summary": "Snowflake hiring senior engineer to lead ROCm production deployment for inference workloads.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Snowflake"}}],
        "raw_metadata_json": {},
    },
    {
        "exa_result_id": "demo-r005",
        "title": "AMD ROCm 6.2 Adoption Report: Enterprise Production Deployments",
        "url": "https://semianalysis.com/rocm-enterprise-2025",
        "domain": "semianalysis.com",
        "published_date": "2025-10-10",
        "author": "Dylan Patel",
        "highlights_json": [
            "ROCm 6.2 shows meaningful adoption in specific inference workloads at hyperscalers.",
            "Most production CUDA code cannot be directly ported without significant engineering effort.",
            "AMD's push for ROCm production adoption remains primarily experimental outside of PyTorch.",
        ],
        "summary": "Analysis of ROCm 6.2 enterprise adoption shows growth in specific niches but CUDA dominance persists.",
        "text": None,
        "entities_json": [],
        "raw_metadata_json": {},
    },
]

DEMO_COMPETITIVE_RESULTS = [
    {
        "exa_result_id": "demo-c001",
        "title": "Oracle Cloud Deploys AMD MI300X for Production AI Inference",
        "url": "https://www.oracle.com/news/announcement/amd-mi300x-oci-2025/",
        "domain": "oracle.com",
        "published_date": "2025-09-05",
        "author": "Oracle Cloud Infrastructure",
        "highlights_json": [
            "Oracle Cloud Infrastructure expands its AI compute portfolio with AMD MI300X instances.",
            "Initial deployment focused on large language model inference workloads for enterprise customers.",
            "OCI will operate both NVIDIA H100 and AMD MI300X fleets in parallel to serve customer demand.",
        ],
        "summary": "Oracle adds AMD MI300X to its production AI compute fleet, running alongside existing NVIDIA H100 capacity.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Oracle"}}],
        "raw_metadata_json": {},
    },
    {
        "exa_result_id": "demo-c002",
        "title": "Hugging Face Expands AMD Inference Endpoints",
        "url": "https://huggingface.co/blog/amd-inference-expansion",
        "domain": "huggingface.co",
        "published_date": "2025-08-14",
        "author": "Hugging Face Team",
        "highlights_json": [
            "Hugging Face now offers AMD MI300X-based inference endpoints as an alternative to NVIDIA.",
            "We are adding AMD infrastructure to reduce costs and offer customers more choice.",
            "Models targeting production deployment should be benchmarked on both platforms.",
        ],
        "summary": "Hugging Face adds AMD MI300X inference endpoints alongside NVIDIA, offering cost-competitive alternatives.",
        "text": None,
        "entities_json": [{"type": "company", "properties": {"name": "Hugging Face"}}],
        "raw_metadata_json": {},
    },
]


async def run_demo_search(req: SearchRequest, db: Session) -> SearchRun:
    """Return deterministic demo results. Clearly marked as DEMO DATA."""
    run = SearchRun(
        company_id=req.company_id,
        signal_id=req.signal_id,
        query=req.query,
        request_json={
            "query": req.query,
            "type": req.search_type,
            "numResults": req.num_results,
            "_demo": True,
            "_note": "DEMO DATA — not real Exa results",
        },
        exa_request_id=f"demo-req-{int(time.time())}",
        search_time_ms=245.0,
        cost_json=None,
        status="completed",
        response_json={"_demo": True, "_note": "DEMO DATA — not real Exa results"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Choose results based on query content
    query_lower = req.query.lower()
    if "rocm" in query_lower or "hiring" in query_lower or "job" in query_lower:
        results_data = DEMO_ROCM_RESULTS[:req.num_results]
    elif "displac" in query_lower or "compet" in query_lower or "adopt" in query_lower:
        results_data = DEMO_COMPETITIVE_RESULTS[:req.num_results]
    else:
        results_data = (DEMO_ROCM_RESULTS + DEMO_COMPETITIVE_RESULTS)[:req.num_results]

    for r in results_data:
        result = SearchResult(search_run_id=run.id, **r)
        db.add(result)

    db.commit()
    db.refresh(run)
    return run
