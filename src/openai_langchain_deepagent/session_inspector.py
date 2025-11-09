"""Session inspection and export utilities."""

from datetime import datetime, timezone
from typing import Dict

from .state import SessionState


def print_session_state(state: SessionState, detailed: bool = False) -> None:
    """
    Print formatted session information.

    Args:
        state: Current session state
        detailed: If True, print detailed information including all recommendations

    Example:
        >>> print_session_state(state)
        Session: ses_20250109_143022_abc123de
        Advisor: adv_001
        Merchant: mch_789456 (TechRetail) [mid_market]
        ...
    """
    # Calculate duration
    started = datetime.fromisoformat(state["started_at"])
    last_activity = datetime.fromisoformat(state["last_activity_at"])
    duration_seconds = (last_activity - started).total_seconds()
    duration_minutes = duration_seconds / 60

    # Header
    print("\n" + "=" * 70)
    print("SESSION STATE")
    print("=" * 70)

    # Session metadata
    print(f"\nAdvisor ID:      {state['advisor_id']}")
    print(
        f"Merchant:        {state['merchant_id']}"
        + (f" ({state['merchant_name']})" if state["merchant_name"] else "")
        + (f" [{state['segment']}]" if state["segment"] else "")
    )
    print(f"Started:         {state['started_at']}")
    print(f"Last Activity:   {state['last_activity_at']}")
    print(f"Duration:        {duration_minutes:.1f} minutes ({duration_seconds:.0f}s)")

    # Metrics
    print(f"\n{'-' * 70}")
    print("METRICS")
    print(f"{'-' * 70}")
    print(f"Total Queries:   {state['total_queries']}")
    print(f"Topics:          {len(state['topics_discussed'])}")
    if state["topics_discussed"]:
        print(f"  Topics list:   {', '.join(state['topics_discussed'])}")

    # Cache info
    print(f"Cached Data:     {len(state['cached_data'])} types")
    if state["cached_data"]:
        print(f"  Data types:    {', '.join(state['cached_data'].keys())}")

    # Recommendations
    print(f"Recommendations: {len(state['recommendations'])}")
    if detailed and state["recommendations"]:
        print(f"\n{'-' * 70}")
        print("RECOMMENDATIONS (DETAILED)")
        print(f"{'-' * 70}")
        for i, rec in enumerate(state["recommendations"], 1):
            print(f"\n  {i}. [{rec['priority'].upper()}] {rec['type']}")
            print(f"     Description: {rec['description']}")
            if rec.get("expected_impact"):
                print(f"     Impact:      {rec['expected_impact']}")
            print(f"     Created:     {rec['created_at']}")

    # Pending questions
    print(f"\nPending Questions: {len(state['pending_questions'])}")
    if state["pending_questions"]:
        for i, question in enumerate(state["pending_questions"], 1):
            print(f"  {i}. {question}")

    # Advisor notes
    print(f"\nAdvisor Notes:   {len(state['advisor_notes'])}")
    if detailed and state["advisor_notes"]:
        print(f"\n{'-' * 70}")
        print("ADVISOR NOTES (DETAILED)")
        print(f"{'-' * 70}")
        for i, note_entry in enumerate(state["advisor_notes"], 1):
            print(f"\n  {i}. {note_entry['timestamp']}")
            print(f"     {note_entry['note']}")

    print("\n" + "=" * 70 + "\n")


def export_session_summary(state: SessionState) -> Dict:
    """
    Export session summary as JSON-serializable dictionary.

    This is designed for future Layer 2 persistence and session handoff.

    Args:
        state: Current session state

    Returns:
        Dictionary with complete session summary

    Example:
        >>> summary = export_session_summary(state)
        >>> json.dumps(summary, indent=2)  # Can be saved to file
    """
    # Calculate duration
    started = datetime.fromisoformat(state["started_at"])
    last_activity = datetime.fromisoformat(state["last_activity_at"])
    duration_seconds = (last_activity - started).total_seconds()

    # Current timestamp for export
    ended_at = datetime.now(timezone.utc).isoformat()

    return {
        # Session metadata
        "advisor_id": state["advisor_id"],
        "started_at": state["started_at"],
        "last_activity_at": state["last_activity_at"],
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        # Merchant info
        "merchant_id": state["merchant_id"],
        "merchant_name": state["merchant_name"],
        "segment": state["segment"],
        # Metrics
        "total_queries": state["total_queries"],
        "topics_discussed": state["topics_discussed"],
        "topics_count": len(state["topics_discussed"]),
        # Cached data info (metadata only, not actual data)
        "cached_data_types": list(state["cached_data"].keys()),
        "cached_at": state["cached_at"],
        # Recommendations
        "recommendations": state["recommendations"],
        "recommendations_count": len(state["recommendations"]),
        # Pending questions
        "pending_questions": state["pending_questions"],
        "pending_questions_count": len(state["pending_questions"]),
        # Advisor notes
        "advisor_notes": state["advisor_notes"],
        "advisor_notes_count": len(state["advisor_notes"]),
        # Working data (scratch space)
        "working_data": state["working_data"],
    }
