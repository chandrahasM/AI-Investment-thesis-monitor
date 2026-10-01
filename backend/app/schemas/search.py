from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any, Dict


class ContentOptions(BaseModel):
    highlights: bool = True
    text: bool = False
    summary: bool = False


class SearchRequest(BaseModel):
    query: str
    search_type: str = "auto"
    num_results: int = 25
    start_published_date: Optional[str] = None
    end_published_date: Optional[str] = None
    include_domains: List[str] = []
    exclude_domains: List[str] = []
    category: Optional[str] = None
    objective: Optional[str] = None
    system_prompt: Optional[str] = None
    content_options: ContentOptions = ContentOptions()
    company_id: Optional[int] = None
    signal_id: Optional[int] = None


class SearchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    search_run_id: int
    exa_result_id: Optional[str] = None
    title: Optional[str] = None
    url: str
    domain: Optional[str] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    highlights: List[str] = []
    summary: Optional[str] = None
    text: Optional[str] = None
    entities: List[Any] = []
    raw_metadata: Optional[Dict[str, Any]] = None


class SearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: Optional[int] = None
    signal_id: Optional[int] = None
    query: str
    request_json: Optional[Dict[str, Any]] = None
    exa_request_id: Optional[str] = None
    search_time_ms: Optional[float] = None
    cost_json: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    results: List[SearchResultResponse] = []
    result_count: int = 0
    is_demo: bool = False
