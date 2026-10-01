from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.company import Company
from app.models.evidence import Evidence
from app.models.signal import Signal
from app.models.thesis import ThesisAssumption
from app.schemas.evidence import InboxFindingResponse

router = APIRouter(tags=["inbox"])


def _enrich_finding(e: Evidence, db: Session) -> InboxFindingResponse:
    signal_name = None
    if e.signal_id:
        sig = db.query(Signal).filter(Signal.id == e.signal_id).first()
        if sig:
            signal_name = sig.name

    assumption_title = None
    if e.assumption_id:
        assumption = db.query(ThesisAssumption).filter(ThesisAssumption.id == e.assumption_id).first()
        if assumption:
            assumption_title = assumption.title

    return InboxFindingResponse(
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
        signal_name=signal_name,
        assumption_title=assumption_title,
    )


@router.get("/api/companies/{ticker}/inbox", response_model=List[InboxFindingResponse])
def get_inbox(
    ticker: str,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    q = db.query(Evidence).filter(Evidence.company_id == company.id)
    if status:
        q = q.filter(Evidence.status == status)
    if direction:
        q = q.filter(Evidence.direction == direction)

    findings = q.order_by(Evidence.created_at.desc()).all()
    return [_enrich_finding(e, db) for e in findings]


@router.post("/api/inbox/{evidence_id}/dismiss", response_model=InboxFindingResponse)
def inbox_dismiss(evidence_id: int, db: Session = Depends(get_db)):
    e = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Finding not found")
    e.status = "dismissed"
    db.commit()
    db.refresh(e)
    return _enrich_finding(e, db)
