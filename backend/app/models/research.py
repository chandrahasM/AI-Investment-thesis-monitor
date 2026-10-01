from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class ResearchRun(Base):
    """One end-to-end thesis research run: ecosystem mapping + per-dimension Exa searches."""

    __tablename__ = "research_runs"

    id = Column(String(32), primary_key=True, index=True)
    company = Column(String(100), nullable=False)
    company_name = Column(String(255), nullable=True)
    thesis = Column(Text, nullable=False)
    mode = Column(String(32), nullable=False)
    lookback_days = Column(Integer, nullable=False, default=90)
    results_per_dimension = Column(Integer, nullable=False, default=8)
    status = Column(String(32), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    events_json = Column(JSON, nullable=False, default=list)
    signals_json = Column(JSON, nullable=False, default=list)
    ecosystem_json = Column(JSON, nullable=True)
    stats_json = Column(JSON, nullable=True)
    people_json = Column(JSON, nullable=True)
    agent_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
