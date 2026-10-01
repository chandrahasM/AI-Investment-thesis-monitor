from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class EvidenceCreate(BaseModel):
    company_id: int
    assumption_id: Optional[int] = None
    signal_id: Optional[int] = None
    search_result_id: Optional[int] = None
    agent_run_id: Optional[int] = None
    title: str
    url: str
    excerpt: Optional[str] = None
    direction: str = "neutral"
    analyst_note: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None


class EvidenceApprove(BaseModel):
    assumption_id: Optional[int] = None
    direction: str
    analyst_note: Optional[str] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    assumption_id: Optional[int] = None
    signal_id: Optional[int] = None
    search_result_id: Optional[int] = None
    agent_run_id: Optional[int] = None
    title: str
    url: str
    excerpt: Optional[str] = None
    direction: str
    status: str
    analyst_note: Optional[str] = None
    source_metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


class InboxFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    assumption_id: Optional[int] = None
    signal_id: Optional[int] = None
    search_result_id: Optional[int] = None
    agent_run_id: Optional[int] = None
    title: str
    url: str
    excerpt: Optional[str] = None
    direction: str
    status: str
    analyst_note: Optional[str] = None
    source_metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    # Enriched fields
    signal_name: Optional[str] = None
    assumption_title: Optional[str] = None
