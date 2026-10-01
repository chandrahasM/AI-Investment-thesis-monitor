from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class ThesisAssumptionBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "insufficient_evidence"


class ThesisAssumptionCreate(ThesisAssumptionBase):
    pass


class ThesisAssumptionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ThesisAssumptionResponse(ThesisAssumptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thesis_id: int
    created_at: datetime
    updated_at: datetime


class ThesisBase(BaseModel):
    thesis_text: str


class ThesisCreate(ThesisBase):
    pass


class ThesisUpdate(BaseModel):
    thesis_text: Optional[str] = None


class ThesisResponse(ThesisBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    assumptions: List[ThesisAssumptionResponse] = []


class SuggestedSignal(BaseModel):
    name: str
    description: str
    signal_type: str
    expected_direction: str
    related_assumption_title: Optional[str] = None


class SuggestSignalsResponse(BaseModel):
    suggestions: List[SuggestedSignal]
