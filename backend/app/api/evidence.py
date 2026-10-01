from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.company import Company
from app.models.evidence import Evidence
from app.models.thesis import ThesisAssumption
from app.models.signal import Signal
from app.schemas.evidence import EvidenceCreate, EvidenceApprove, EvidenceResponse

router = APIRouter(tags=["evidence"])


def _enrich_evidence(e: Evidence, db: Session) -> EvidenceResponse:
    return EvidenceResponse(
        id=e.id,
        company_id=e.company_id,
        assumption_id=e.assumption_id,
        signal_id=e.signal_id,
        search_result_id=e.search_result_id,
        agent_run_id=e.agent_run_id,
        title=e.title,
        url=e.url,
        excerpt=e.excerpt,
        direction=e.direction,
        status=e.status,
        analyst_note=e.analyst_note,
        source_metadata_json=e.source_metadata_json,
        created_at=e.created_at,
        approved_at=e.approved_at,
    )


@router.get("/api/companies/{ticker}/evidence", response_model=List[EvidenceResponse])
def list_evidence(ticker: str, status: str = None, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    q = db.query(Evidence).filter(Evidence.company_id == company.id)
    if status:
        q = q.filter(Evidence.status == status)
    return [_enrich_evidence(e, db) for e in q.order_by(Evidence.created_at.desc()).all()]


@router.post("/api/evidence", response_model=EvidenceResponse)
def create_evidence(payload: EvidenceCreate, db: Session = Depends(get_db)):
    evidence = Evidence(
        company_id=payload.company_id,
        assumption_id=payload.assumption_id,
        signal_id=payload.signal_id,
        search_result_id=payload.search_result_id,
        agent_run_id=payload.agent_run_id,
        title=payload.title,
        url=payload.url,
        excerpt=payload.excerpt,
        direction=payload.direction,
        analyst_note=payload.analyst_note,
        source_metadata_json=payload.source_metadata,
        status="candidate",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return _enrich_evidence(evidence, db)


@router.post("/api/evidence/{evidence_id}/approve", response_model=EvidenceResponse)
def approve_evidence(evidence_id: int, payload: EvidenceApprove, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence.status = "approved"
    evidence.direction = payload.direction
    evidence.approved_at = datetime.utcnow()
    if payload.analyst_note:
        evidence.analyst_note = payload.analyst_note
    if payload.assumption_id:
        evidence.assumption_id = payload.assumption_id
    db.commit()
    db.refresh(evidence)

    # Update assumption status based on evidence balance
    _recalculate_assumption_status(evidence.assumption_id, db)
    return _enrich_evidence(evidence, db)


@router.post("/api/evidence/{evidence_id}/dismiss", response_model=EvidenceResponse)
def dismiss_evidence(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence.status = "dismissed"
    db.commit()
    db.refresh(evidence)
    return _enrich_evidence(evidence, db)


def _recalculate_assumption_status(assumption_id: int, db: Session):
    """Recalculate assumption evidence status based on approved evidence."""
    if not assumption_id:
        return
    assumption = db.query(ThesisAssumption).filter(ThesisAssumption.id == assumption_id).first()
    if not assumption:
        return

    approved = db.query(Evidence).filter(
        Evidence.assumption_id == assumption_id,
        Evidence.status == "approved"
    ).all()

    if not approved:
        assumption.status = "insufficient_evidence"
    else:
        directions = [e.direction for e in approved]
        supporting = directions.count("supporting")
        contradicting = directions.count("contradicting")
        if supporting > 0 and contradicting == 0:
            assumption.status = "supporting"
        elif contradicting > 0 and supporting == 0:
            assumption.status = "challenged"
        elif supporting > 0 and contradicting > 0:
            assumption.status = "mixed"
        else:
            assumption.status = "insufficient_evidence"

    db.commit()
