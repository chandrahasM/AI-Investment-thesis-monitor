from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theses = relationship("Thesis", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="company", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")
    tracked_entities = relationship("TrackedEntity", back_populates="company", cascade="all, delete-orphan")
    search_runs = relationship("SearchRun", back_populates="company", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="company", cascade="all, delete-orphan")
    activity_events = relationship("ActivityEvent", back_populates="company", cascade="all, delete-orphan")
