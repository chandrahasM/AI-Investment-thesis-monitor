"""
Demo Agent Service — deterministic fixtures for NVDA demo.
Never mixed with real Exa responses.
"""

import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.agent import AgentRunCreate
from app.models.agent import AgentRun


DEMO_JOB_ENRICHMENT = {
    "structured": {
        "company": "Snowflake",
        "role": "Senior GPU Software Engineer — ROCm Production Systems",
        "job_url": "https://careers.snowflake.com/jobs/senior-gpu-rocm",
        "location": "San Mateo, CA / Remote",
        "rocm_required": True,
        "cuda_required": True,
        "production_context": "Will lead migration of select inference workloads to AMD MI300X infrastructure. Role explicitly mentions production ROCm deployments.",
        "workload": "Large language model inference",
        "evidence": "Job posting explicitly requests 5+ years production ROCm/CUDA experience and mentions leading inference migration to AMD MI300X.",
        "published_date": "2025-09-28",
        "existing_nvidia_relationship": "Snowflake currently uses NVIDIA H100s for the majority of its AI workloads.",
        "evidence_direction": "mixed",
        "open_questions": [
            "What fraction of Snowflake inference workloads are being moved vs. kept on NVIDIA?",
            "Is this a cost-optimization experiment or a strategic platform shift?",
            "Has Snowflake made a public commitment to AMD as a primary compute partner?",
        ],
    },
    "text": "Snowflake is hiring a Senior GPU Software Engineer to lead deployment of AMD MI300X for production inference. The role requires both ROCm and CUDA experience. This is notable because Snowflake is a significant NVIDIA customer. However, the job description suggests AMD will be used alongside, not instead of, NVIDIA infrastructure — indicating a complementary deployment rather than displacement.",
    "grounding": [
        {"field": "job_url", "citations": [{"url": "https://careers.snowflake.com/jobs/senior-gpu-rocm", "title": "Senior GPU Software Engineer - ROCm Production Systems"}], "confidence": "high"},
        {"field": "existing_nvidia_relationship", "citations": [{"url": "https://www.snowflake.com/en/data-cloud/workloads/ai-ml/", "title": "Snowflake AI & ML Workloads"}], "confidence": "medium"},
    ],
}

DEMO_COMPETITIVE_ENRICHMENT = {
    "structured": {
        "company": "Oracle",
        "signal_type": "competitive_displacement",
        "event_date": "2025-09-05",
        "existing_relationship": "Oracle Cloud Infrastructure operates one of the largest NVIDIA H100 fleets outside of hyperscalers. OCI and NVIDIA have a formal partnership.",
        "competing_product": "AMD MI300X",
        "workload": "Large language model inference",
        "deployment_scale": "Fleet-scale — multiple OCI regions",
        "replacement_or_complementary": "Complementary — OCI is adding AMD capacity alongside existing NVIDIA H100 fleet, not replacing it.",
        "finding": "Oracle confirmed AMD MI300X deployment for production LLM inference, but explicitly stated NVIDIA H100 and AMD MI300X fleets will operate in parallel. No evidence of NVIDIA capacity reduction.",
        "evidence_direction": "neutral",
        "open_questions": [
            "What share of new OCI AI compute capacity is being allocated to AMD vs. NVIDIA?",
            "Are there specific customer workloads that Oracle is steering toward AMD?",
            "Does OCI's AMD expansion create pricing pressure on NVIDIA H100 instances?",
        ],
    },
    "text": "Oracle's AMD MI300X deployment is confirmed for production LLM inference, but this represents capacity addition rather than NVIDIA displacement. OCI is running a dual-vendor strategy. This is consistent with hyperscaler behavior of maintaining multi-vendor optionality. The evidence direction is neutral — it confirms AMD production viability but does not demonstrate NVIDIA customer loss.",
    "grounding": [
        {"field": "replacement_or_complementary", "citations": [{"url": "https://www.oracle.com/news/announcement/amd-mi300x-oci-2025/", "title": "Oracle Cloud Infrastructure Expands AI Compute with AMD MI300X"}], "confidence": "high"},
        {"field": "existing_relationship", "citations": [{"url": "https://www.nvidia.com/en-us/data-center/oci/", "title": "NVIDIA and Oracle Cloud Infrastructure Partnership"}], "confidence": "high"},
    ],
}


async def create_demo_agent_run(req: AgentRunCreate, db: Session) -> AgentRun:
    """Return a completed demo agent run with fixture data."""
    run = AgentRun(
        company_id=req.company_id,
        signal_id=req.signal_id,
        search_result_id=req.search_result_id,
        query=req.query,
        effort=req.effort,
        system_prompt=req.system_prompt,
        input_data_json=req.input_data,
        output_schema_json=req.output_schema,
        status="completed",
        exa_agent_id=f"demo-agent-{int(time.time())}",
        completed_at=datetime.now(timezone.utc),
        raw_response_json={"_demo": True, "_note": "DEMO DATA — not real Exa Agent output"},
    )

    query_lower = req.query.lower()
    if "job" in query_lower or "hiring" in query_lower or "rocm" in query_lower:
        fixture = DEMO_JOB_ENRICHMENT
    else:
        fixture = DEMO_COMPETITIVE_ENRICHMENT

    run.output_json = fixture["structured"]
    run.output_text = fixture["text"]
    run.grounding_json = fixture["grounding"]
    run.cost_json = {"total": {"minimal": 0.012, "low": 0.025, "medium": 0.10, "high": 0.50, "xhigh": 1.00}.get(req.effort, 0.10)}

    db.add(run)
    db.commit()
    db.refresh(run)
    return run
