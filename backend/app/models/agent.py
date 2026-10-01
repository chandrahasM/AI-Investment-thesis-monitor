from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    search_result_id = Column(Integer, ForeignKey("search_results.id"), nullable=True)
    exa_agent_id = Column(String(255), nullable=True)
    query = Column(Text, nullable=False)
    effort = Column(String(50), default="medium")
    system_prompt = Column(Text, nullable=True)
    input_data_json = Column(JSON, nullable=True)
    output_schema_json = Column(JSON, nullable=True)
    output_json = Column(JSON, nullable=True)
    output_text = Column(Text, nullable=True)
    grounding_json = Column(JSON, nullable=True)
    raw_response_json = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, queued, running, completed, failed
    cost_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="agent_runs")
    signal = relationship("Signal", back_populates="agent_runs")
    search_result = relationship("SearchResult", back_populates="agent_runs")
    evidence = relationship("Evidence", back_populates="agent_run")
