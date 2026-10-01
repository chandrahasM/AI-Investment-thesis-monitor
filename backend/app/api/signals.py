from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.evidence import Evidence
from app.models.search import SearchRun
from app.schemas.signal import SignalCreate, SignalUpdate, SignalResponse

router = APIRouter(tags=["signals"])


def _enrich_signal(signal: Signal, db: Session) -> SignalResponse:
    """Add computed counts to a Signal."""
    candidate_count = db.query(Evidence).filter(
        Evidence.signal_id == signal.id,
        Evidence.status == "candidate"
    ).count()
    validated_count = db.query(Evidence).filter(
        Evidence.signal_id == signal.id,
        Evidence.status.in_(["approved", "dismissed"])
    ).count()
    approved_count = db.query(Evidence).filter(
        Evidence.signal_id == signal.id,
        Evidence.status == "approved"
    ).count()
    last_run = db.query(SearchRun).filter(
        SearchRun.signal_id == signal.id,
        SearchRun.status == "completed"
    ).order_by(SearchRun.created_at.desc()).first()

    resp = SignalResponse.model_validate(signal)
    resp.candidate_count = candidate_count
    resp.validated_count = validated_count
    resp.approved_count = approved_count
    resp.last_researched_at = last_run.created_at if last_run else None
    return resp


@router.get("/api/companies/{ticker}/signals", response_model=List[SignalResponse])
def list_signals(ticker: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    signals = db.query(Signal).filter(Signal.company_id == company.id).all()
    return [_enrich_signal(s, db) for s in signals]


@router.post("/api/companies/{ticker}/signals", response_model=SignalResponse)
def create_signal(ticker: str, payload: SignalCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    signal = Signal(company_id=company.id, **payload.model_dump())
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return _enrich_signal(signal, db)


@router.get("/api/signals/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _enrich_signal(signal, db)


@router.patch("/api/signals/{signal_id}", response_model=SignalResponse)
def update_signal(signal_id: int, payload: SignalUpdate, db: Session = Depends(get_db)):
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(signal, field, value)
    signal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(signal)
    return _enrich_signal(signal, db)


@router.delete("/api/signals/{signal_id}")
def delete_signal(signal_id: int, db: Session = Depends(get_db)):
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    db.delete(signal)
    db.commit()
    return {"ok": True}
