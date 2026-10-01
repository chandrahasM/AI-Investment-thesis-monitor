from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SearchRun(Base):
    __tablename__ = "search_runs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    query = Column(Text, nullable=False)
    request_json = Column(JSON, nullable=True)
    response_json = Column(JSON, nullable=True)
    exa_request_id = Column(String(255), nullable=True)
    search_time_ms = Column(Float, nullable=True)
    cost_json = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="search_runs")
    signal = relationship("Signal", back_populates="search_runs")
    results = relationship("SearchResult", back_populates="search_run", cascade="all, delete-orphan")


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, index=True)
    search_run_id = Column(Integer, ForeignKey("search_runs.id"), nullable=False)
    exa_result_id = Column(String(255), nullable=True)
    title = Column(String(1000), nullable=True)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=True)
    published_date = Column(String(100), nullable=True)
    author = Column(String(255), nullable=True)
    highlights_json = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    entities_json = Column(JSON, nullable=True)
    raw_metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    search_run = relationship("SearchRun", back_populates="results")
    agent_runs = relationship("AgentRun", back_populates="search_result")
    evidence = relationship("Evidence", back_populates="search_result")
