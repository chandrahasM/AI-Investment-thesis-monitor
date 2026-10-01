from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class SignalSearchConfigBase(BaseModel):
    search_type: str = "auto"
    num_results: int = 25
    start_published_date: Optional[str] = None
    end_published_date: Optional[str] = None
    include_domains: List[str] = []
    exclude_domains: List[str] = []
    category: Optional[str] = None
    objective: Optional[str] = None
    system_prompt: Optional[str] = None
    content_options: dict = {}


class SignalBase(BaseModel):
    name: str
    description: str
    signal_type: str
    expected_direction: str = "unknown"
    research_strategy: str = "auto"


class SignalCreate(SignalBase):
    assumption_id: Optional[int] = None


class SignalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    signal_type: Optional[str] = None
    expected_direction: Optional[str] = None
    research_strategy: Optional[str] = None
    status: Optional[str] = None
    monitor_enabled: Optional[bool] = None
    assumption_id: Optional[int] = None


class SignalResponse(SignalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    assumption_id: Optional[int] = None
    status: str
    monitor_enabled: bool
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0
    validated_count: int = 0
    approved_count: int = 0
    last_researched_at: Optional[datetime] = None
