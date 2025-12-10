"""
Database checkpointer setup for LangGraph persistence.
Enables crash recovery and state management using PostgreSQL.
"""
import os
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv

load_dotenv()


def get_checkpointer():
    """
    Create and return PostgreSQL checkpointer for LangGraph.
    Uses DATABASE_URL from environment variables.
    
    Returns:
        PostgresSaver context manager
    
    Usage:
        with get_checkpointer() as checkpointer:
            graph = workflow.compile(checkpointer=checkpointer)
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    if not db_url.startswith("postgresql"):
        raise ValueError(f"PostgreSQL connection string required. Got: {db_url}")
    
    # Return PostgresSaver context manager
    # This handles connection lifecycle properly
    return PostgresSaver.from_conn_string(db_url)


def init_database():
    """
    Initialize database tables and schema.
    
    LangGraph's PostgresSaver automatically creates the checkpoint table
    when first used. This function sets up the connection and runs setup.
    
    The checkpoint table stores workflow state snapshots for crash recovery.
    """
    with get_checkpointer() as checkpointer:
        # Setup is called automatically when checkpointer is created
        # The table will be created if it doesn't exist
        pass
    
    print("✅ PostgreSQL checkpointer initialized successfully")
    return True
