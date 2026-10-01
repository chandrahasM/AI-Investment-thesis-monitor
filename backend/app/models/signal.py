from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    assumption_id = Column(Integer, ForeignKey("thesis_assumptions.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    signal_type = Column(String(100), nullable=False)
    expected_direction = Column(String(50), default="unknown")  # supporting, contradicting, unknown
    research_strategy = Column(String(50), default="auto")  # broad_web, primary_sources, independent, custom
    status = Column(String(50), default="active")  # active, paused, archived
    monitor_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="signals")
    assumption = relationship("ThesisAssumption", back_populates="signals")
    search_configs = relationship("SignalSearchConfig", back_populates="signal", cascade="all, delete-orphan")
    search_runs = relationship("SearchRun", back_populates="signal")
    agent_runs = relationship("AgentRun", back_populates="signal")
    evidence = relationship("Evidence", back_populates="signal")


class SignalSearchConfig(Base):
    __tablename__ = "signal_search_configs"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    search_type = Column(String(50), default="auto")
    num_results = Column(Integer, default=25)
    start_published_date = Column(String(50), nullable=True)
    end_published_date = Column(String(50), nullable=True)
    include_domains_json = Column(JSON, default=list)
    exclude_domains_json = Column(JSON, default=list)
    category = Column(String(50), nullable=True)
    objective = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    content_options_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    signal = relationship("Signal", back_populates="search_configs")
