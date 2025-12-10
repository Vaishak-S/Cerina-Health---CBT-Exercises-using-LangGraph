"""
Database checkpointer setup for LangGraph persistence.
Enables crash recovery and state management using PostgreSQL.
"""
import os
from typing import Optional
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

# Global connection pool and checkpointer
_pool = None
_checkpointer = None


def get_connection_pool():
    """Get or create the global connection pool."""
    global _pool
    
    if _pool is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        _pool = ConnectionPool(
            conninfo=db_url,
            max_size=10,
            kwargs={"autocommit": True, "prepare_threshold": 0}
        )
    
    return _pool


def get_checkpointer():
    """
    Get or create PostgreSQL checkpointer for LangGraph.
    
    Returns:
        PostgresSaver instance
    """
    global _checkpointer
    
    if _checkpointer is not None:
        return _checkpointer
    
    pool = get_connection_pool()
    _checkpointer = PostgresSaver(pool)
    
    return _checkpointer


def init_database():
    """
    Initialize database tables and schema.
    
    Returns:
        PostgresSaver instance with setup completed
    """
    checkpointer = get_checkpointer()
    checkpointer.setup()
    return checkpointer
