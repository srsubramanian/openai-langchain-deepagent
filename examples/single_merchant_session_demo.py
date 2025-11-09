"""Demo of Layer 1 Session Memory - Single Merchant Conversations.

This example demonstrates:
- Starting a session for a single merchant
- Running multiple queries with conversation memory
- Managing session state (topics, recommendations, notes)
- Inspecting and exporting session data
- Merchant ID validation
"""

import json
import os
import sys

from openai_langchain_deepagent.agent import (
    run_query_in_session,
    start_merchant_session,
)
from openai_langchain_deepagent.session_inspector import (
    export_session_summary,
    print_session_state,
)
from openai_langchain_deepagent.session_manager import (
    add_advisor_note,
    add_recommendation,
    add_topic,
    validate_merchant_match,
)


def demo_single_merchant_session():
    """
    Demo: Complete session lifecycle for a single merchant.

    Shows how to:
    1. Start a merchant session
    2. Run multiple queries with memory
    3. Track topics and add recommendations
    4. Inspect session state
    5. Export session summary
    """
    print("=" * 70)
    print("LAYER 1 SESSION MEMORY DEMO: Single Merchant Conversation")
    print("=" * 70)
    print()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set it in your .env file")
        sys.exit(1)

    # Start a session for merchant 789456
    print("Starting session for merchant 789456 (TechRetail, mid_market)...")
    agent, thread_id, state = start_merchant_session(
        advisor_id="adv_001",
        merchant_id="789456",  # Will be normalized to mch_789456
        merchant_name="TechRetail",
        segment="mid_market",
    )
    print(f"✓ Session started: {state['session_id']}")
    print(f"✓ Thread ID: {thread_id}")
    print(f"✓ Merchant: {state['merchant_id']}")
    print()

    # Query 1: Ask about merchant status
    print("-" * 70)
    print("Query 1: What can you tell me about this merchant?")
    print("-" * 70)
    response, state = run_query_in_session(
        agent=agent,
        thread_id=thread_id,
        session_state=state,
        query="I'm working with merchant TechRetail (mch_789456). What should I know?",
    )
    print(f"Response: {response[:200]}...")  # Truncate for demo
    print()

    # Add topic
    state = add_topic(state, "merchant_overview")
    print("✓ Added topic: merchant_overview")
    print()

    # Query 2: Ask about decline rates
    print("-" * 70)
    print("Query 2: What about their decline rates?")
    print("-" * 70)
    response, state = run_query_in_session(
        agent=agent,
        thread_id=thread_id,
        session_state=state,
        query="What are the typical causes of high decline rates for mid-market merchants?",
    )
    print(f"Response: {response[:200]}...")
    print()

    # Add topic and recommendation
    state = add_topic(state, "decline_rates")
    state = add_recommendation(
        state=state,
        recommendation_type="decline_optimization",
        priority="high",
        description="Review fraud filter settings - may be too aggressive for mid-market segment",
        expected_impact="Could reduce false positives by 15-20%",
    )
    print("✓ Added topic: decline_rates")
    print("✓ Added recommendation: Review fraud filter settings")
    print()

    # Query 3: Follow-up question (tests conversation memory)
    print("-" * 70)
    print("Query 3: What specific steps should I take? (tests memory)")
    print("-" * 70)
    response, state = run_query_in_session(
        agent=agent,
        thread_id=thread_id,
        session_state=state,
        query="What specific steps should I take to address this?",
    )
    print(f"Response: {response[:200]}...")
    print()

    # Add advisor note
    state = add_advisor_note(
        state=state, note="Merchant expressed interest in decline rate optimization"
    )
    print("✓ Added advisor note")
    print()

    # Query 4: Another topic
    print("-" * 70)
    print("Query 4: Ask about transaction volume")
    print("-" * 70)
    response, state = run_query_in_session(
        agent=agent,
        thread_id=thread_id,
        session_state=state,
        query="What's typical transaction volume for mid-market merchants?",
    )
    print(f"Response: {response[:200]}...")
    print()

    state = add_topic(state, "transaction_volume")
    print("✓ Added topic: transaction_volume")
    print()

    # Print session state (detailed)
    print_session_state(state, detailed=True)

    # Export session summary
    print("Exporting session summary...")
    summary = export_session_summary(state)
    print("\nSession Summary (JSON):")
    print(json.dumps(summary, indent=2))
    print()

    print("=" * 70)
    print("✓ Demo complete!")
    print("=" * 70)


def demo_merchant_validation():
    """
    Demo: Merchant ID validation in sessions.

    Shows how to validate that queries are about the correct merchant.
    """
    print("\n\n")
    print("=" * 70)
    print("MERCHANT VALIDATION DEMO")
    print("=" * 70)
    print()

    # Start session for merchant A
    print("Starting session for merchant mch_111111...")
    agent, thread_id, state = start_merchant_session(
        advisor_id="adv_002",
        merchant_id="mch_111111",
        merchant_name="ShopA",
        segment="small_business",
    )
    print(f"✓ Session started for: {state['merchant_id']}")
    print()

    # Validate correct merchant
    print("Validating merchant mch_111111 (should match)...")
    is_valid = validate_merchant_match(state, "mch_111111")
    print(f"  Result: {'✓ VALID' if is_valid else '❌ INVALID'}")
    print()

    # Validate wrong merchant
    print("Validating merchant mch_222222 (should NOT match)...")
    is_valid = validate_merchant_match(state, "mch_222222")
    print(f"  Result: {'✓ VALID' if is_valid else '❌ INVALID'}")
    print()

    # Test without mch_ prefix
    print("Validating merchant 111111 (without prefix, should match)...")
    is_valid = validate_merchant_match(state, "111111")
    print(f"  Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print()

    print("=" * 70)
    print("✓ Validation demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    # Run the main demo
    demo_single_merchant_session()

    # Run validation demo
    demo_merchant_validation()
