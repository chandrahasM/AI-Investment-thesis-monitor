from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.company import Company
from app.models.thesis import Thesis, ThesisAssumption
from app.models.evidence import Evidence
from app.schemas.thesis import (
    ThesisResponse, ThesisUpdate,
    ThesisAssumptionResponse, ThesisAssumptionCreate, ThesisAssumptionUpdate,
    SuggestSignalsResponse, SuggestedSignal,
)

router = APIRouter(tags=["thesis"])

NVDA_SUGGESTED_SIGNALS = [
    SuggestedSignal(name="ROCm Developer Tooling Growth", description="Find evidence of growing ROCm developer tooling, libraries, and documentation.", signal_type="technology_adoption", expected_direction="contradicting", related_assumption_title="CUDA remains the preferred software ecosystem"),
    SuggestedSignal(name="Custom Silicon Production Milestones", description="Find hyperscaler announcements of production milestones for TPUs, Trainium, Maia, or other custom AI silicon.", signal_type="competitive_displacement", expected_direction="contradicting", related_assumption_title="Hyperscaler custom silicon remains more complementary than substitutive"),
    SuggestedSignal(name="CUDA Developer Community Growth", description="Find evidence of expanding CUDA developer community: certifications, courses, conferences, GitHub activity.", signal_type="technology_adoption", expected_direction="supporting", related_assumption_title="CUDA remains the preferred software ecosystem"),
    SuggestedSignal(name="AI Infrastructure Contract Announcements", description="Find public announcements of large AI infrastructure contracts specifying accelerator platforms.", signal_type="customer_expansion", expected_direction="supporting", related_assumption_title="Major customers are not materially migrating production workloads"),
    SuggestedSignal(name="NVIDIA Executive Departures", description="Find departures of key NVIDIA executives with knowledge of enterprise relationships or competitive strategy.", signal_type="people_change", expected_direction="unknown", related_assumption_title=None),
]


@router.get("/api/companies/{ticker}/thesis", response_model=ThesisResponse)
def get_thesis(ticker: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    thesis = db.query(Thesis).filter(Thesis.company_id == company.id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="No thesis found for this company")
    return thesis


@router.put("/api/theses/{thesis_id}", response_model=ThesisResponse)
def update_thesis(thesis_id: int, payload: ThesisUpdate, db: Session = Depends(get_db)):
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    if payload.thesis_text is not None:
        thesis.thesis_text = payload.thesis_text
    db.commit()
    db.refresh(thesis)
    return thesis


@router.get("/api/theses/{thesis_id}/assumptions", response_model=List[ThesisAssumptionResponse])
def get_assumptions(thesis_id: int, db: Session = Depends(get_db)):
    return db.query(ThesisAssumption).filter(ThesisAssumption.thesis_id == thesis_id).all()


@router.post("/api/theses/{thesis_id}/assumptions", response_model=ThesisAssumptionResponse)
def create_assumption(thesis_id: int, payload: ThesisAssumptionCreate, db: Session = Depends(get_db)):
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    assumption = ThesisAssumption(thesis_id=thesis_id, **payload.model_dump())
    db.add(assumption)
    db.commit()
    db.refresh(assumption)
    return assumption


@router.patch("/api/assumptions/{assumption_id}", response_model=ThesisAssumptionResponse)
def update_assumption(assumption_id: int, payload: ThesisAssumptionUpdate, db: Session = Depends(get_db)):
    assumption = db.query(ThesisAssumption).filter(ThesisAssumption.id == assumption_id).first()
    if not assumption:
        raise HTTPException(status_code=404, detail="Assumption not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(assumption, field, value)
    db.commit()
    db.refresh(assumption)
    return assumption


@router.post("/api/theses/{thesis_id}/suggest-signals", response_model=SuggestSignalsResponse)
def suggest_signals(thesis_id: int, db: Session = Depends(get_db)):
    """Suggest semantic signals for a thesis. Returns deterministic NVDA suggestions."""
    thesis = db.query(Thesis).filter(Thesis.id == thesis_id).first()
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return SuggestSignalsResponse(suggestions=NVDA_SUGGESTED_SIGNALS)


@router.get("/api/assumptions/{assumption_id}/evidence")
def get_assumption_evidence(assumption_id: int, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(
        Evidence.assumption_id == assumption_id,
        Evidence.status == "approved"
    ).all()
    return evidence
