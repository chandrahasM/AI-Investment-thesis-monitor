from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.company import Company
from app.models.thesis import Thesis
from app.schemas.company import CompanyResponse, CompanyCreate

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=List[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()


@router.get("/{ticker}", response_model=CompanyResponse)
def get_company(ticker: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return company


@router.post("", response_model=CompanyResponse)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.ticker == payload.ticker.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    company = Company(**payload.model_dump())
    company.ticker = company.ticker.upper()
    db.add(company)
    db.flush()

    # Auto-create a blank thesis for every new company
    blank_thesis = Thesis(
        company_id=company.id,
        thesis_text=f"Enter your investment thesis for {company.ticker} here.",
    )
    db.add(blank_thesis)
    db.commit()
    db.refresh(company)
    return company
