"""
Database models for storing protocol generation history.
"""
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class ProtocolHistory(Base):
    """Store all protocol generation requests and results"""
    __tablename__ = "protocol_history"
    
    id = Column(String, primary_key=True)
    user_intent = Column(Text, nullable=False)
    user_context = Column(Text, nullable=True)
    final_protocol = Column(Text, nullable=True)
    iteration_count = Column(Integer, default=0)
    human_approved = Column(Boolean, default=False)
    human_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    state_snapshot = Column(JSON, nullable=True)


class AgentInteraction(Base):
    """Log all agent interactions and scratchpad entries"""
    __tablename__ = "agent_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(String, nullable=False, index=True)
    agent_role = Column(String, nullable=False)
    iteration = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SafetyLog(Base):
    """Track all safety assessments"""
    __tablename__ = "safety_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(String, nullable=False, index=True)
    safety_level = Column(String, nullable=False)
    concerns = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Database session management
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cerina_foundry.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_history_db():
    """Initialize history database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
