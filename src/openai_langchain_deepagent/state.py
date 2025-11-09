"""State definitions for session memory management."""

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import add_messages
from typing_extensions import Annotated


class SessionState(TypedDict):
    """Single merchant session state.

    One session = one merchant conversation.
    All context, cache, and history for a specific merchant.
    """

    # LangGraph built-in message handling
    messages: Annotated[List, add_messages]

    # Session metadata (uses thread_id as identifier)
    advisor_id: str
    started_at: str  # ISO timestamp
    last_activity_at: str  # ISO timestamp

    # Merchant context (single merchant per session)
    merchant_id: str
    merchant_name: Optional[str]
    segment: Optional[str]  # "small_business", "mid_market", "enterprise"

    # Session metrics
    total_queries: int

    # Data caching
    cached_data: Dict[str, dict]  # {data_type: data}
    cached_at: Dict[str, str]  # {data_type: ISO timestamp}

    # Conversation tracking
    topics_discussed: List[str]
    recommendations: List[Dict[str, Any]]
    pending_questions: List[str]
    advisor_notes: List[Dict[str, str]]  # [{"note": str, "timestamp": str}]

    # Working data (scratch space for agent)
    working_data: Dict[str, Any]


class CacheConfig(TypedDict):
    """TTL configuration for different data types."""

    profile_ttl_seconds: int
    metrics_ttl_seconds: int
    transactions_ttl_seconds: int
    alerts_ttl_seconds: int
