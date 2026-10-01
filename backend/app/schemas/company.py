from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class CompanyBase(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
