from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    assumption_id = Column(Integer, ForeignKey("thesis_assumptions.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    search_result_id = Column(Integer, ForeignKey("search_results.id"), nullable=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=True)
    title = Column(String(1000), nullable=False)
    url = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    direction = Column(String(50), default="neutral")  # supporting, contradicting, neutral, insufficient
    status = Column(String(50), default="candidate")  # candidate, approved, dismissed
    analyst_note = Column(Text, nullable=True)
    source_metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="evidence")
    assumption = relationship("ThesisAssumption", back_populates="evidence")
    signal = relationship("Signal", back_populates="evidence")
    search_result = relationship("SearchResult", back_populates="evidence")
    agent_run = relationship("AgentRun", back_populates="evidence")


class TrackedEntity(Base):
    __tablename__ = "tracked_entities"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)  # person, company, technology
    relationship_type = Column(String(100), nullable=True)
    source = Column(Text, nullable=True)
    tracked = Column(Integer, default=1)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="tracked_entities")


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="activity_events")
