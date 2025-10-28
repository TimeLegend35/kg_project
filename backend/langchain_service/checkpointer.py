"""
LangChain PostgresSaver for automatic conversation persistence
"""
import os
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection


def get_postgres_checkpointer():
    """
    Create and return a PostgresSaver instance for conversation persistence.

    This automatically saves all conversation states to PostgreSQL.
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "langgraph.checkpoint.postgres is not installed. "
            "Install it with: pip install langgraph-checkpoint-postgres"
        )

    db_url = os.getenv(
        "DB_URL",
        "postgresql://bgb_user:bgb_password@localhost:5432/bgb_chat"
    )

    # Convert SQLAlchemy URL format to psycopg format if needed
    if "postgresql+psycopg" in db_url:
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://")

    # Create connection
    conn = Connection.connect(db_url, autocommit=True)

    # Create checkpointer with the connection
    checkpointer = PostgresSaver(conn)

    # Setup tables (creates checkpoint tables if they don't exist)
    checkpointer.setup()

    return checkpointer


def get_checkpointer_config(thread_id: str) -> dict:
    """
    Get configuration for checkpointer with thread_id.

    Args:
        thread_id: The thread/conversation ID

    Returns:
        Configuration dict for use with LangGraph
    """
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }

