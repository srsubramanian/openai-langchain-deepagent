"""Utilities for managing conversation sessions with checkpointing."""

import sqlite3
from typing import Any, Dict, List, Optional


def get_session_history(
    thread_id: str, db_path: str = "checkpoints.db"
) -> List[Dict[str, Any]]:
    """
    Retrieve conversation history for a given thread/session.

    Args:
        thread_id: The thread ID to retrieve history for
        db_path: Path to the SQLite checkpoint database

    Returns:
        List of checkpoint records for the session

    Example:
        >>> history = get_session_history("user-123")
        >>> print(f"Found {len(history)} checkpoints")
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT * FROM checkpoints
            WHERE thread_id = ?
            ORDER BY checkpoint_id
            """,
            (thread_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []
    finally:
        conn.close()


def list_active_sessions(db_path: str = "checkpoints.db") -> List[str]:
    """
    List all active session thread IDs.

    Args:
        db_path: Path to the SQLite checkpoint database

    Returns:
        List of unique thread IDs

    Example:
        >>> sessions = list_active_sessions()
        >>> print(f"Active sessions: {sessions}")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT DISTINCT thread_id FROM checkpoints
            ORDER BY thread_id
            """
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []
    finally:
        conn.close()


def clear_session(thread_id: str, db_path: str = "checkpoints.db") -> int:
    """
    Delete all checkpoints for a given session.

    Args:
        thread_id: The thread ID to clear
        db_path: Path to the SQLite checkpoint database

    Returns:
        Number of checkpoints deleted

    Example:
        >>> deleted = clear_session("user-123")
        >>> print(f"Deleted {deleted} checkpoints")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM checkpoints
            WHERE thread_id = ?
            """,
            (thread_id,),
        )
        conn.commit()
        return cursor.rowcount
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0
    finally:
        conn.close()


def get_session_info(
    thread_id: str, db_path: str = "checkpoints.db"
) -> Optional[Dict[str, Any]]:
    """
    Get metadata about a session.

    Args:
        thread_id: The thread ID to get info for
        db_path: Path to the SQLite checkpoint database

    Returns:
        Dictionary with session metadata or None if not found

    Example:
        >>> info = get_session_info("user-123")
        >>> if info:
        >>>     print(f"Session has {info['checkpoint_count']} checkpoints")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                thread_id,
                COUNT(*) as checkpoint_count,
                MIN(checkpoint_id) as first_checkpoint,
                MAX(checkpoint_id) as last_checkpoint
            FROM checkpoints
            WHERE thread_id = ?
            GROUP BY thread_id
            """,
            (thread_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "thread_id": row[0],
                "checkpoint_count": row[1],
                "first_checkpoint": row[2],
                "last_checkpoint": row[3],
            }
        return None
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return None
    finally:
        conn.close()


def clear_all_sessions(db_path: str = "checkpoints.db") -> int:
    """
    Delete all checkpoints from all sessions.

    Args:
        db_path: Path to the SQLite checkpoint database

    Returns:
        Number of checkpoints deleted

    Example:
        >>> deleted = clear_all_sessions()
        >>> print(f"Deleted {deleted} total checkpoints")
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM checkpoints")
        conn.commit()
        return cursor.rowcount
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0
    finally:
        conn.close()
