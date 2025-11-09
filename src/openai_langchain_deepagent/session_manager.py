"""Session management functions for single-merchant conversations."""

import re
from datetime import datetime, timezone
from typing import Dict, Optional

from .state import CacheConfig, SessionState

# Default cache TTL configuration
DEFAULT_CACHE_CONFIG: CacheConfig = {
    "profile_ttl_seconds": 1800,  # 30 minutes
    "metrics_ttl_seconds": 300,  # 5 minutes
    "transactions_ttl_seconds": 60,  # 1 minute
    "alerts_ttl_seconds": 30,  # 30 seconds
}


def initialize_session_state(
    advisor_id: str,
    merchant_id: str,
    merchant_name: Optional[str] = None,
    segment: Optional[str] = None,
) -> SessionState:
    """
    Initialize a new session state for a merchant.

    Session is identified by thread_id (merchant_{merchant_id}_{timestamp})
    which is created by start_merchant_session().

    Args:
        advisor_id: ID of the advisor starting the session
        merchant_id: Merchant ID for this session
        merchant_name: Optional merchant name
        segment: Optional segment ("small_business", "mid_market", "enterprise")

    Returns:
        Initialized SessionState

    Example:
        >>> state = initialize_session_state("adv_001", "mch_789456", "TechRetail", "mid_market")
        >>> state["merchant_id"]  # "mch_789456"
    """
    # Normalize merchant_id to have mch_ prefix
    if not merchant_id.startswith("mch_"):
        merchant_id = f"mch_{merchant_id}"

    now = datetime.now(timezone.utc)
    iso_timestamp = now.isoformat()

    return SessionState(
        messages=[],
        advisor_id=advisor_id,
        started_at=iso_timestamp,
        last_activity_at=iso_timestamp,
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        segment=segment,
        total_queries=0,
        cached_data={},
        cached_at={},
        topics_discussed=[],
        recommendations=[],
        pending_questions=[],
        advisor_notes=[],
        working_data={},
    )


def extract_merchant_id(text: str) -> Optional[str]:
    """
    Extract merchant ID from text using regex patterns.

    Supports formats:
    - "merchant 789456"
    - "mch_789456"
    - "merchant ID 789456"
    - "m789456"

    Args:
        text: Input text to search

    Returns:
        Normalized merchant ID with "mch_" prefix, or None if not found

    Example:
        >>> extract_merchant_id("Check merchant 789456 status")
        'mch_789456'
        >>> extract_merchant_id("mch_123 has issues")
        'mch_123'
    """
    patterns = [
        r"mch_(\d+)",  # mch_789456
        r"merchant\s+id\s+(\d+)",  # merchant ID 789456
        r"merchant\s+(\d+)",  # merchant 789456
        r"m(\d+)",  # m789456
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            merchant_num = match.group(1)
            return f"mch_{merchant_num}"

    return None


def increment_query_count(state: SessionState) -> SessionState:
    """
    Increment query count and update last activity timestamp.

    Args:
        state: Current session state

    Returns:
        Updated session state
    """
    updated_state = state.copy()
    updated_state["total_queries"] = state["total_queries"] + 1
    updated_state["last_activity_at"] = datetime.now(timezone.utc).isoformat()
    return updated_state


def cache_data(state: SessionState, data_type: str, data: dict) -> SessionState:
    """
    Cache data for a specific data type.

    Args:
        state: Current session state
        data_type: Type of data (e.g., "profile", "metrics", "transactions", "alerts")
        data: Data to cache

    Returns:
        Updated session state
    """
    updated_state = state.copy()
    updated_state["cached_data"] = state["cached_data"].copy()
    updated_state["cached_at"] = state["cached_at"].copy()

    updated_state["cached_data"][data_type] = data
    updated_state["cached_at"][data_type] = datetime.now(timezone.utc).isoformat()

    return updated_state


def get_cached_data(
    state: SessionState,
    data_type: str,
    cache_config: CacheConfig = DEFAULT_CACHE_CONFIG,
) -> Optional[dict]:
    """
    Get cached data if not expired, with Phoenix tracing.

    Args:
        state: Current session state
        data_type: Type of data to retrieve
        cache_config: Cache TTL configuration

    Returns:
        Cached data if fresh, None if expired or not found

    Example:
        >>> state = cache_data(state, "profile", {"name": "TechRetail"})
        >>> get_cached_data(state, "profile")  # Returns the profile data
        >>> time.sleep(1801)
        >>> get_cached_data(state, "profile")  # Returns None (expired)
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)
        span = tracer.start_span("cache_lookup")
    except (ImportError, Exception):
        tracer = None
        span = None

    try:
        # Add trace attributes
        if span:
            span.set_attribute("cache.data_type", data_type)

        # Check if data exists
        if data_type not in state["cached_data"]:
            if span:
                span.set_attribute("cache.hit", False)
                span.set_attribute("cache.miss_reason", "not_found")
            return None

        # Get TTL for this data type
        ttl_key = f"{data_type}_ttl_seconds"
        ttl = cache_config.get(ttl_key, 300)  # Default 5 minutes

        # Calculate age
        cached_time = datetime.fromisoformat(state["cached_at"][data_type])
        current_time = datetime.now(timezone.utc)
        age_seconds = (current_time - cached_time).total_seconds()

        if span:
            span.set_attribute("cache.age_seconds", age_seconds)
            span.set_attribute("cache.ttl_seconds", ttl)

        # Check if expired
        if age_seconds > ttl:
            if span:
                span.set_attribute("cache.hit", False)
                span.set_attribute("cache.miss_reason", "expired")
            return None

        # Cache hit!
        if span:
            span.set_attribute("cache.hit", True)

        return state["cached_data"][data_type]

    finally:
        if span:
            span.end()


def add_topic(state: SessionState, topic: str) -> SessionState:
    """
    Add a discussion topic (no duplicates).

    Args:
        state: Current session state
        topic: Topic to add (will be normalized)

    Returns:
        Updated session state

    Example:
        >>> state = add_topic(state, "Decline Rates")
        >>> state = add_topic(state, "decline rates")  # Duplicate, not added
        >>> len(state["topics_discussed"])
        1
    """
    updated_state = state.copy()
    updated_state["topics_discussed"] = state["topics_discussed"].copy()

    # Normalize: lowercase, replace spaces with underscores
    normalized = topic.lower().replace(" ", "_")

    # Add if not duplicate
    if normalized not in updated_state["topics_discussed"]:
        updated_state["topics_discussed"].append(normalized)

    return updated_state


def add_recommendation(
    state: SessionState,
    recommendation_type: str,
    priority: str,
    description: str,
    expected_impact: Optional[str] = None,
) -> SessionState:
    """
    Add a recommendation to the session.

    Args:
        state: Current session state
        recommendation_type: Type of recommendation
        priority: Priority level ("high", "medium", "low")
        description: Description of the recommendation
        expected_impact: Optional expected impact

    Returns:
        Updated session state
    """
    updated_state = state.copy()
    updated_state["recommendations"] = state["recommendations"].copy()

    recommendation = {
        "type": recommendation_type,
        "priority": priority,
        "description": description,
        "expected_impact": expected_impact,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    updated_state["recommendations"].append(recommendation)
    return updated_state


def add_pending_question(state: SessionState, question: str) -> SessionState:
    """
    Add a pending question (no duplicates).

    Args:
        state: Current session state
        question: Question to add

    Returns:
        Updated session state
    """
    updated_state = state.copy()
    updated_state["pending_questions"] = state["pending_questions"].copy()

    if question not in updated_state["pending_questions"]:
        updated_state["pending_questions"].append(question)

    return updated_state


def add_advisor_note(state: SessionState, note: str) -> SessionState:
    """
    Add an advisor note with timestamp.

    Args:
        state: Current session state
        note: Note content

    Returns:
        Updated session state
    """
    updated_state = state.copy()
    updated_state["advisor_notes"] = state["advisor_notes"].copy()

    note_entry = {
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    updated_state["advisor_notes"].append(note_entry)
    return updated_state


def get_session_summary(state: SessionState) -> Dict:
    """
    Get a summary of the session.

    Args:
        state: Current session state

    Returns:
        Dictionary with session summary metrics

    Example:
        >>> summary = get_session_summary(state)
        >>> summary["duration_seconds"]
        3600
    """
    started = datetime.fromisoformat(state["started_at"])
    last_activity = datetime.fromisoformat(state["last_activity_at"])
    duration_seconds = (last_activity - started).total_seconds()

    return {
        "advisor_id": state["advisor_id"],
        "merchant_id": state["merchant_id"],
        "merchant_name": state["merchant_name"],
        "segment": state["segment"],
        "started_at": state["started_at"],
        "last_activity_at": state["last_activity_at"],
        "duration_seconds": duration_seconds,
        "total_queries": state["total_queries"],
        "topics_count": len(state["topics_discussed"]),
        "topics": state["topics_discussed"],
        "recommendations_count": len(state["recommendations"]),
        "pending_questions_count": len(state["pending_questions"]),
        "advisor_notes_count": len(state["advisor_notes"]),
        "cached_data_types": list(state["cached_data"].keys()),
    }


def validate_merchant_match(state: SessionState, merchant_id: str) -> bool:
    """
    Validate that merchant ID matches the session's merchant.

    Args:
        state: Current session state
        merchant_id: Merchant ID to validate

    Returns:
        True if matches, False otherwise

    Example:
        >>> state = initialize_session_state("adv_001", "mch_789456")
        >>> validate_merchant_match(state, "mch_789456")
        True
        >>> validate_merchant_match(state, "mch_111111")
        False
    """
    # Normalize merchant_id
    if not merchant_id.startswith("mch_"):
        merchant_id = f"mch_{merchant_id}"

    return state["merchant_id"] == merchant_id


def create_session_snapshot(state: SessionState, thread_id: str) -> Dict:
    """
    Create a snapshot of current session state for OpenTelemetry tracing.

    This snapshot is designed to be attached to OpenTelemetry spans as attributes
    or events, providing visibility into session evolution in Phoenix.

    Args:
        state: Current session state
        thread_id: Thread ID for this session (merchant_{merchant_id}_{timestamp})

    Returns:
        Dictionary with session snapshot suitable for tracing

    Example:
        >>> from opentelemetry import trace
        >>> snapshot = create_session_snapshot(state, thread_id)
        >>> span = trace.get_current_span()
        >>> span.add_event("session_snapshot", attributes=snapshot)
    """
    started = datetime.fromisoformat(state["started_at"])
    last_activity = datetime.fromisoformat(state["last_activity_at"])
    duration_seconds = (last_activity - started).total_seconds()

    # Calculate cache ages
    cache_ages = {}
    now = datetime.now(timezone.utc)
    for data_type, cached_timestamp in state["cached_at"].items():
        cached_at = datetime.fromisoformat(cached_timestamp)
        age = (now - cached_at).total_seconds()
        cache_ages[f"cache_age_{data_type}"] = age

    snapshot = {
        # Session metadata (using thread_id as identifier)
        "session.thread_id": thread_id,
        "session.advisor_id": state["advisor_id"],
        "session.total_queries": state["total_queries"],
        "session.duration_seconds": duration_seconds,
        # Merchant context
        "merchant.id": state["merchant_id"],
        "merchant.name": state.get("merchant_name") or "",
        "merchant.segment": state.get("segment") or "",
        # Conversation tracking
        "session.topics_count": len(state["topics_discussed"]),
        "session.topics": ", ".join(state["topics_discussed"]),
        "session.recommendations_count": len(state["recommendations"]),
        "session.pending_questions_count": len(state["pending_questions"]),
        "session.advisor_notes_count": len(state["advisor_notes"]),
        # Cache state
        "session.cached_data_types": ", ".join(state["cached_data"].keys()),
        "session.cached_types_count": len(state["cached_data"]),
    }

    # Add cache ages
    snapshot.update(cache_ages)

    return snapshot
