"""
Seed script — populates SQLite with NVDA demo data.
Run: python -m app.db.seed
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
import app.models  # noqa — ensure all models are registered


def seed_nvda(db: Session):
    from app.models.company import Company
    from app.models.thesis import Thesis, ThesisAssumption
    from app.models.signal import Signal

    # Idempotent: skip if NVDA already exists
    existing = db.query(Company).filter(Company.ticker == "NVDA").first()
    if existing:
        print("NVDA already seeded, skipping.")
        return

    # Company
    company = Company(
        ticker="NVDA",
        name="NVIDIA Corporation",
        sector="Semiconductors",
        description=(
            "NVIDIA Corporation designs and manufactures graphics processing units (GPUs) "
            "and system-on-chip units. It is the dominant provider of AI accelerator hardware "
            "and the CUDA software ecosystem."
        ),
    )
    db.add(company)
    db.flush()

    # Thesis
    thesis = Thesis(
        company_id=company.id,
        thesis_text=(
            "NVIDIA's CUDA ecosystem and developer lock-in will allow it to maintain "
            "dominant economics in AI accelerators despite increasing competition."
        ),
    )
    db.add(thesis)
    db.flush()

    # Assumptions
    assumptions_data = [
        {
            "title": "CUDA remains the preferred software ecosystem for production AI workloads",
            "description": (
                "The majority of production AI training and inference continues to target CUDA "
                "rather than competing frameworks such as AMD ROCm or vendor-specific SDKs."
            ),
            "status": "supporting",
        },
        {
            "title": "Major customers are not materially migrating production workloads to competing accelerator ecosystems",
            "description": (
                "Large hyperscalers and enterprise AI customers have not made material shifts "
                "of existing production CUDA workloads to AMD, Intel, or custom accelerator platforms."
            ),
            "status": "mixed",
        },
        {
            "title": "AMD ROCm adoption remains limited relative to CUDA",
            "description": (
                "Despite AMD's investment in ROCm, developer mindshare, available tooling, "
                "and production deployment remain significantly below CUDA."
            ),
            "status": "mixed",
        },
        {
            "title": "Hyperscaler custom silicon remains more complementary than substitutive",
            "description": (
                "Google TPUs, AWS Trainium/Inferentia, and Microsoft Maia are used alongside "
                "NVIDIA hardware, not as replacements for the bulk of CUDA workloads."
            ),
            "status": "insufficient_evidence",
        },
        {
            "title": "NVIDIA's developer ecosystem remains difficult to replicate",
            "description": (
                "The depth of CUDA libraries (cuDNN, cuBLAS, NCCL, TensorRT), developer tools, "
                "and community knowledge represents a durable moat."
            ),
            "status": "supporting",
        },
    ]

    assumptions = []
    for a in assumptions_data:
        assumption = ThesisAssumption(
            thesis_id=thesis.id,
            title=a["title"],
            description=a["description"],
            status=a["status"],
        )
        db.add(assumption)
        assumptions.append(assumption)
    db.flush()

    # Signals
    signals_data = [
        {
            "name": "ROCm Production Hiring",
            "description": "Find AI infrastructure companies hiring engineers with production AMD ROCm experience.",
            "signal_type": "job_activity",
            "expected_direction": "contradicting",
            "research_strategy": "broad_web",
            "assumption_idx": 0,
        },
        {
            "name": "Alternative Accelerator Adoption",
            "description": "Find existing NVIDIA customers moving production AI workloads to AMD accelerators or internally designed AI accelerators.",
            "signal_type": "competitive_displacement",
            "expected_direction": "contradicting",
            "research_strategy": "independent",
            "assumption_idx": 1,
        },
        {
            "name": "CUDA Ecosystem Expansion",
            "description": "Find companies publicly expanding production workloads, developer tooling, infrastructure, or engineering investment around CUDA.",
            "signal_type": "technology_adoption",
            "expected_direction": "supporting",
            "research_strategy": "broad_web",
            "assumption_idx": 0,
        },
        {
            "name": "AI Infrastructure Leadership Changes",
            "description": "Find meaningful changes in AI infrastructure leadership at strategically important NVIDIA customers or competitors.",
            "signal_type": "people_change",
            "expected_direction": "unknown",
            "research_strategy": "primary_sources",
            "assumption_idx": 1,
        },
    ]

    for s in signals_data:
        assumption_id = assumptions[s["assumption_idx"]].id
        signal = Signal(
            company_id=company.id,
            assumption_id=assumption_id,
            name=s["name"],
            description=s["description"],
            signal_type=s["signal_type"],
            expected_direction=s["expected_direction"],
            research_strategy=s["research_strategy"],
            status="active",
        )
        db.add(signal)

    db.commit()
    print("NVDA seed data inserted.")


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_nvda(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
