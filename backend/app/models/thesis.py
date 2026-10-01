from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Thesis(Base):
    __tablename__ = "theses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    thesis_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="theses")
    assumptions = relationship("ThesisAssumption", back_populates="thesis", cascade="all, delete-orphan")


class ThesisAssumption(Base):
    __tablename__ = "thesis_assumptions"

    id = Column(Integer, primary_key=True, index=True)
    thesis_id = Column(Integer, ForeignKey("theses.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="insufficient_evidence")  # supporting, mixed, challenged, insufficient_evidence
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    thesis = relationship("Thesis", back_populates="assumptions")
    signals = relationship("Signal", back_populates="assumption")
    evidence = relationship("Evidence", back_populates="assumption")
