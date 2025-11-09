"""
Debug script to show exactly what attributes are on your Phoenix spans.

This helps diagnose why messages might show as "undefined".
"""

import os
import sys
import time


def run_test_and_show_expected_attributes():
    """Run a test query and show what attributes should be in Phoenix."""
    print("=" * 80)
    print("PHOENIX ATTRIBUTES DEBUG - Running Test Query")
    print("=" * 80)
    print()

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        sys.exit(1)

    try:
        from openai_langchain_deepagent.agent import (
            run_query_in_session,
            start_merchant_session,
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    # Start a test session
    print("1️⃣  Starting test session...")
    agent, thread_id, state = start_merchant_session(
        advisor_id="debug_test",
        merchant_id="999999",
        merchant_name="Debug Merchant",
        segment="mid_market",
    )

    session_id = state["session_id"]
    print(f"   ✓ Session ID: {session_id}")
    print(f"   ✓ Thread ID: {thread_id}")
    print()

    # Run a test query
    print("2️⃣  Running test query...")
    test_query = "What is the capital of France?"
    print(f"   Query: {test_query}")
    print()

    response, state = run_query_in_session(
        agent=agent, thread_id=thread_id, session_state=state, query=test_query
    )

    print(f"   Response: {response[:100]}...")
    print()

    # Give Phoenix time to receive the trace
    print("3️⃣  Waiting for trace to arrive in Phoenix (5 seconds)...")
    time.sleep(5)
    print()

    # Show what should be in Phoenix
    print("=" * 80)
    print("EXPECTED ATTRIBUTES IN PHOENIX")
    print("=" * 80)
    print()
    print("🔍 In Phoenix UI, filter by:")
    print(f"   session.id = \"{session_id}\"")
    print()
    print("📍 You should see a span named: merchant_query")
    print()
    print("👉 Click on that span and check the Attributes tab for:")
    print()

    # Show expected attributes
    expected_attributes = {
        "Session Identifiers": {
            "session.id": session_id,
            "session.thread_id": thread_id,
            "session.advisor_id": "debug_test",
            "session.query_number": 1,
        },
        "Merchant Context": {
            "merchant.id": "mch_999999",
            "merchant.name": "Debug Merchant",
            "merchant.segment": "mid_market",
        },
        "Messages (THESE ARE WHAT YOU WANT!)": {
            "input.value": test_query,
            "output.value": response[:50] + "...",
            "input.mime_type": "text/plain",
            "output.mime_type": "text/plain",
        },
        "Response Metadata": {
            "response.length": len(response),
        },
        "Session State": {
            "session.total_queries": 1,
            "session.topics_count": 0,
            "session.recommendations_count": 0,
            "session.duration_seconds": "(some value)",
        },
    }

    for category, attrs in expected_attributes.items():
        print(f"\n📂 {category}")
        print("-" * 80)
        for key, value in attrs.items():
            print(f"   {key}: {value}")

    print()
    print("=" * 80)
    print("EXPECTED EVENTS IN PHOENIX")
    print("=" * 80)
    print()
    print("👉 Click on the span and check the Events tab for:")
    print()

    events = {
        "user_message": {
            "message.role": "user",
            "message.content": test_query,
            "session.query_number": 1,
        },
        "session_snapshot_before": {
            "session.total_queries": 0,
            "session.topics_count": 0,
            "(many other fields)": "...",
        },
        "assistant_message": {
            "message.role": "assistant",
            "message.content": response[:50] + "...",
        },
        "session_snapshot_after": {
            "session.total_queries": 1,
            "session.topics_count": 0,
            "(many other fields)": "...",
        },
    }

    for event_name, event_attrs in events.items():
        print(f"\n📌 Event: {event_name}")
        print("-" * 80)
        for key, value in event_attrs.items():
            print(f"   {key}: {value}")

    print()
    print("=" * 80)
    print("HOW TO CHECK")
    print("=" * 80)
    print()
    print("1. Open Phoenix UI: http://localhost:6006")
    print()
    print("2. In the filter box, enter:")
    print(f"   session.id = \"{session_id}\"")
    print()
    print("3. You should see ONE trace with a 'merchant_query' span")
    print()
    print("4. Click on the 'merchant_query' span (the parent, NOT child spans)")
    print()
    print("5. Go to 'Attributes' tab and look for:")
    print("   - input.value (should show the query)")
    print("   - output.value (should show the response)")
    print()
    print("6. If you see 'undefined' instead:")
    print("   a) Make sure you clicked on 'merchant_query' parent span")
    print("   b) Check if you're scrolled down far enough (many attributes)")
    print("   c) Try Events tab instead - look for 'user_message' event")
    print()
    print("7. Alternative: Filter by thread ID:")
    print(f"   session.thread_id = \"{thread_id}\"")
    print()


def show_span_hierarchy():
    """Show the expected span hierarchy in Phoenix."""
    print("\n" + "=" * 80)
    print("SPAN HIERARCHY IN PHOENIX")
    print("=" * 80)
    print()
    print("When you run a query, Phoenix creates this span hierarchy:")
    print()
    print("merchant_query (parent span)           ← MESSAGES ARE HERE!")
    print("├─ Attributes:")
    print("│  ├─ input.value: <user query>        ← USER MESSAGE")
    print("│  ├─ output.value: <AI response>      ← AI RESPONSE")
    print("│  ├─ session.id: ses_...")
    print("│  ├─ merchant.id: mch_...")
    print("│  └─ ... (many more)")
    print("│")
    print("├─ Events:")
    print("│  ├─ user_message                     ← ALSO HAS USER MESSAGE")
    print("│  ├─ session_snapshot_before")
    print("│  ├─ assistant_message                ← ALSO HAS AI RESPONSE")
    print("│  └─ session_snapshot_after")
    print("│")
    print("└─ Child spans (from LangChain auto-instrumentation):")
    print("   ├─ RunnableSequence")
    print("   ├─ ChatOpenAI")
    print("   │  ├─ llm.input_messages            ← Different format")
    print("   │  └─ llm.output_messages           ← Different format")
    print("   └─ ...")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Messages on parent span: input.value / output.value")
    print("   - Messages on child spans: llm.input_messages / llm.output_messages")
    print("   - If filtering by session.id, you MUST click the parent 'merchant_query'")
    print()


def show_common_mistakes():
    """Show common mistakes when looking for messages."""
    print("\n" + "=" * 80)
    print("COMMON MISTAKES")
    print("=" * 80)
    print()

    mistakes = [
        (
            "❌ Clicking on child spans instead of parent",
            "✅ Click on 'merchant_query' parent span, not 'RunnableSequence' or 'ChatOpenAI'",
        ),
        (
            "❌ Looking for wrong attribute names",
            "✅ It's 'input.value' and 'output.value' (lowercase, with dot)",
        ),
        (
            "❌ Not scrolling down in Attributes tab",
            "✅ There are many attributes, scroll down or use Ctrl+F to search",
        ),
        (
            "❌ Filtering by wrong session ID",
            "✅ Use session.id (ses_...) or session.thread_id (merchant_...)",
        ),
        (
            "❌ Phoenix not running or not receiving traces",
            "✅ Check: docker compose ps | grep phoenix",
        ),
        (
            "❌ Looking at old traces from before the fix",
            "✅ Run a new test query after the latest code changes",
        ),
    ]

    for mistake, fix in mistakes:
        print(f"{mistake}")
        print(f"   {fix}")
        print()


if __name__ == "__main__":
    print()
    print("This script will:")
    print("1. Run a test query")
    print("2. Show you exactly what should be in Phoenix")
    print("3. Give you step-by-step instructions")
    print()

    response = input("Press ENTER to continue or Ctrl+C to cancel...")
    print()

    run_test_and_show_expected_attributes()
    show_span_hierarchy()
    show_common_mistakes()

    print()
    print("=" * 80)
    print("✅ Debug info complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Open Phoenix UI: http://localhost:6006")
    print("2. Use the session.id shown above to filter")
    print("3. Click on the 'merchant_query' span")
    print("4. Check Attributes tab for input.value and output.value")
    print()
