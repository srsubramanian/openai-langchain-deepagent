"""Tests for Layer 1 Session Memory - Single Merchant Conversations."""

import time
from datetime import datetime, timezone

import pytest

from openai_langchain_deepagent.session_inspector import (
    export_session_summary,
    print_session_state,
)
from openai_langchain_deepagent.session_manager import (
    DEFAULT_CACHE_CONFIG,
    add_advisor_note,
    add_pending_question,
    add_recommendation,
    add_topic,
    cache_data,
    extract_merchant_id,
    get_cached_data,
    get_session_summary,
    increment_query_count,
    initialize_session_state,
    validate_merchant_match,
)
from openai_langchain_deepagent.state import SessionState


class TestSessionManager:
    """Tests for session_manager.py functions."""

    def test_initialize_session_state(self):
        """Test session state initialization."""
        state = initialize_session_state(
            advisor_id="adv_001",
            merchant_id="789456",
            merchant_name="TechRetail",
            segment="mid_market",
        )

        # Check session ID format: ses_YYYYMMDD_HHMMSS_{8char_uuid}
        assert state["session_id"].startswith("ses_")
        parts = state["session_id"].split("_")
        assert len(parts) == 4  # ses, YYYYMMDD, HHMMSS, uuid
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 8  # 8 char uuid

        # Check merchant_id normalization
        assert state["merchant_id"] == "mch_789456"

        # Check basic fields
        assert state["advisor_id"] == "adv_001"
        assert state["merchant_name"] == "TechRetail"
        assert state["segment"] == "mid_market"
        assert state["total_queries"] == 0
        assert state["messages"] == []
        assert state["cached_data"] == {}
        assert state["topics_discussed"] == []
        assert state["recommendations"] == []

        # Check timestamps are ISO format
        datetime.fromisoformat(state["started_at"])  # Should not raise
        datetime.fromisoformat(state["last_activity_at"])  # Should not raise

    def test_extract_merchant_id(self):
        """Test merchant ID extraction from text."""
        # Format: mch_XXXXXX
        assert extract_merchant_id("Check mch_789456 status") == "mch_789456"

        # Format: merchant XXXXXX
        assert extract_merchant_id("merchant 789456 has issues") == "mch_789456"

        # Format: merchant ID XXXXXX
        assert extract_merchant_id("merchant ID 123456") == "mch_123456"

        # Format: mXXXXXX
        assert extract_merchant_id("Look at m999888") == "mch_999888"

        # Case insensitive
        assert extract_merchant_id("MERCHANT 111222") == "mch_111222"

        # Not found
        assert extract_merchant_id("No merchant here") is None

    def test_increment_query_count(self):
        """Test query count increment and timestamp update."""
        state = initialize_session_state("adv_001", "mch_123")

        assert state["total_queries"] == 0
        original_timestamp = state["last_activity_at"]

        # Small delay to ensure timestamp changes
        time.sleep(0.01)

        # Increment
        updated_state = increment_query_count(state)

        assert updated_state["total_queries"] == 1
        assert updated_state["last_activity_at"] != original_timestamp

        # Increment again
        updated_state = increment_query_count(updated_state)
        assert updated_state["total_queries"] == 2

    def test_cache_data_and_retrieval(self):
        """Test caching data and retrieving it."""
        state = initialize_session_state("adv_001", "mch_123")

        # Cache profile data
        profile_data = {"name": "TechRetail", "industry": "Retail"}
        state = cache_data(state, "profile", profile_data)

        # Verify cached
        assert "profile" in state["cached_data"]
        assert state["cached_data"]["profile"] == profile_data
        assert "profile" in state["cached_at"]

        # Retrieve cached data (should not be expired)
        retrieved = get_cached_data(state, "profile", DEFAULT_CACHE_CONFIG)
        assert retrieved == profile_data

    def test_cache_expiration(self):
        """Test that cached data expires based on TTL."""
        state = initialize_session_state("adv_001", "mch_123")

        # Cache data with very short TTL
        test_config = {
            "profile_ttl_seconds": 1,  # 1 second TTL
            "metrics_ttl_seconds": 300,
            "transactions_ttl_seconds": 60,
            "alerts_ttl_seconds": 30,
        }

        profile_data = {"name": "TechRetail"}
        state = cache_data(state, "profile", profile_data)

        # Should be available immediately
        retrieved = get_cached_data(state, "profile", test_config)
        assert retrieved == profile_data

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        retrieved = get_cached_data(state, "profile", test_config)
        assert retrieved is None

    def test_add_topic_no_duplicates(self):
        """Test adding topics with duplicate prevention."""
        state = initialize_session_state("adv_001", "mch_123")

        # Add first topic
        state = add_topic(state, "Decline Rates")
        assert len(state["topics_discussed"]) == 1
        assert "decline_rates" in state["topics_discussed"]

        # Add duplicate (different case, spaces)
        state = add_topic(state, "decline rates")
        assert len(state["topics_discussed"]) == 1  # No duplicate

        # Add different topic
        state = add_topic(state, "Transaction Volume")
        assert len(state["topics_discussed"]) == 2
        assert "transaction_volume" in state["topics_discussed"]

    def test_add_recommendation(self):
        """Test adding recommendations."""
        state = initialize_session_state("adv_001", "mch_123")

        # Add recommendation
        state = add_recommendation(
            state=state,
            recommendation_type="decline_optimization",
            priority="high",
            description="Review fraud settings",
            expected_impact="Reduce false positives by 15%",
        )

        assert len(state["recommendations"]) == 1
        rec = state["recommendations"][0]
        assert rec["type"] == "decline_optimization"
        assert rec["priority"] == "high"
        assert rec["description"] == "Review fraud settings"
        assert rec["expected_impact"] == "Reduce false positives by 15%"
        assert "created_at" in rec

        # Add another
        state = add_recommendation(
            state=state,
            recommendation_type="volume_increase",
            priority="medium",
            description="Marketing campaign",
        )
        assert len(state["recommendations"]) == 2

    def test_add_pending_question(self):
        """Test adding pending questions."""
        state = initialize_session_state("adv_001", "mch_123")

        state = add_pending_question(state, "What is the refund rate?")
        assert len(state["pending_questions"]) == 1
        assert "What is the refund rate?" in state["pending_questions"]

        # Add duplicate - should not be added
        state = add_pending_question(state, "What is the refund rate?")
        assert len(state["pending_questions"]) == 1

        # Add different question
        state = add_pending_question(state, "What is the chargeback rate?")
        assert len(state["pending_questions"]) == 2

    def test_add_advisor_note(self):
        """Test adding advisor notes."""
        state = initialize_session_state("adv_001", "mch_123")

        state = add_advisor_note(state, "Merchant seems interested in optimization")
        assert len(state["advisor_notes"]) == 1
        note = state["advisor_notes"][0]
        assert note["note"] == "Merchant seems interested in optimization"
        assert "timestamp" in note

    def test_get_session_summary(self):
        """Test getting session summary."""
        state = initialize_session_state("adv_001", "mch_789456", "TechRetail")

        # Add some data
        state = add_topic(state, "decline_rates")
        state = add_topic(state, "volume")
        state = add_recommendation(
            state, "test", "high", "Test recommendation", "Test impact"
        )
        state = add_pending_question(state, "What is X?")
        state = add_advisor_note(state, "Note 1")
        state = cache_data(state, "profile", {"name": "Test"})
        state = increment_query_count(state)
        state = increment_query_count(state)

        summary = get_session_summary(state)

        assert summary["session_id"] == state["session_id"]
        assert summary["advisor_id"] == "adv_001"
        assert summary["merchant_id"] == "mch_789456"
        assert summary["merchant_name"] == "TechRetail"
        assert summary["total_queries"] == 2
        assert summary["topics_count"] == 2
        assert summary["recommendations_count"] == 1
        assert summary["pending_questions_count"] == 1
        assert summary["advisor_notes_count"] == 1
        assert "profile" in summary["cached_data_types"]
        assert "duration_seconds" in summary

    def test_validate_merchant_match(self):
        """Test merchant ID validation."""
        state = initialize_session_state("adv_001", "mch_789456")

        # Exact match
        assert validate_merchant_match(state, "mch_789456") is True

        # Without prefix (should normalize)
        assert validate_merchant_match(state, "789456") is True

        # Different merchant
        assert validate_merchant_match(state, "mch_111111") is False
        assert validate_merchant_match(state, "111111") is False


class TestSessionInspector:
    """Tests for session_inspector.py functions."""

    def test_print_session_state(self, capsys):
        """Test printing session state."""
        state = initialize_session_state(
            "adv_001", "mch_789456", "TechRetail", "mid_market"
        )
        state = add_topic(state, "decline_rates")
        state = add_recommendation(
            state, "optimization", "high", "Test rec", "Test impact"
        )

        # Test basic print
        print_session_state(state, detailed=False)
        captured = capsys.readouterr()
        assert "SESSION STATE" in captured.out
        assert "mch_789456" in captured.out
        assert "TechRetail" in captured.out

        # Test detailed print
        print_session_state(state, detailed=True)
        captured = capsys.readouterr()
        assert "RECOMMENDATIONS (DETAILED)" in captured.out
        assert "Test rec" in captured.out

    def test_export_session_summary(self):
        """Test exporting session summary."""
        state = initialize_session_state(
            "adv_001", "mch_789456", "TechRetail", "mid_market"
        )
        state = add_topic(state, "decline_rates")
        state = add_recommendation(state, "optimization", "high", "Test rec")
        state = add_pending_question(state, "What is X?")

        summary = export_session_summary(state)

        # Check all required fields
        assert summary["session_id"] == state["session_id"]
        assert summary["advisor_id"] == "adv_001"
        assert summary["merchant_id"] == "mch_789456"
        assert summary["merchant_name"] == "TechRetail"
        assert summary["segment"] == "mid_market"
        assert summary["started_at"] == state["started_at"]
        assert summary["last_activity_at"] == state["last_activity_at"]
        assert "ended_at" in summary
        assert "duration_seconds" in summary
        assert summary["total_queries"] == 0
        assert summary["topics_count"] == 1
        assert summary["recommendations_count"] == 1
        assert summary["pending_questions_count"] == 1
        assert "decline_rates" in summary["topics_discussed"]
        assert len(summary["recommendations"]) == 1
        assert "What is X?" in summary["pending_questions"]

        # Verify it's JSON serializable
        import json

        json.dumps(summary)  # Should not raise
