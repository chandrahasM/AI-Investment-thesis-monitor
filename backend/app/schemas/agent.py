from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any, Dict


class AgentRunCreate(BaseModel):
    query: str
    effort: str = "medium"
    system_prompt: Optional[str] = None
    output_schema: Optional[Dict[str, Any]] = None
    input_data: Optional[List[Dict[str, Any]]] = None
    company_id: Optional[int] = None
    signal_id: Optional[int] = None
    search_result_id: Optional[int] = None


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: Optional[int] = None
    signal_id: Optional[int] = None
    search_result_id: Optional[int] = None
    exa_agent_id: Optional[str] = None
    query: str
    effort: str
    system_prompt: Optional[str] = None
    input_data_json: Optional[List[Dict[str, Any]]] = None
    output_schema_json: Optional[Dict[str, Any]] = None
    output_json: Optional[Any] = None
    output_text: Optional[str] = None
    grounding_json: Optional[List[Any]] = None
    status: str
    cost_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    is_demo: bool = False


class EnrichRequest(BaseModel):
    search_result_id: int
    company_id: Optional[int] = None
    signal_id: Optional[int] = None
    effort: str = "medium"
