"""
Phoenix Message Troubleshooting Guide

This script helps diagnose and fix "undefined" message issues in Phoenix UI.
"""

import os
import sys


def check_phoenix_setup():
    """Check Phoenix configuration and connectivity."""
    print("=" * 80)
    print("PHOENIX MESSAGE TROUBLESHOOTING")
    print("=" * 80)
    print()

    # Check environment variables
    print("1️⃣  Environment Configuration:")
    print(f"   PHOENIX_ENABLED: {os.getenv('PHOENIX_ENABLED', 'true')}")
    print(f"   PHOENIX_ENDPOINT: {os.getenv('PHOENIX_ENDPOINT', 'http://localhost:4317')}")
    print(f"   OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ NOT SET'}")
    print()

    # Check if Phoenix is running
    print("2️⃣  Phoenix Service Check:")
    print("   Run: docker compose ps")
    print("   Expected: phoenix service should be 'Up'")
    print("   UI should be accessible at: http://localhost:6006")
    print()

    # Check instrumentation
    print("3️⃣  Instrumentation Check:")
    try:
        from openai_langchain_deepagent.instrumentation import is_instrumented

        if is_instrumented():
            print("   ✓ Phoenix instrumentation is active")
        else:
            print("   ✗ Phoenix instrumentation is NOT active")
            print("   → Set PHOENIX_ENABLED=true in .env")
    except Exception as e:
        print(f"   ✗ Error checking instrumentation: {e}")
    print()

    # Message visibility tips
    print("4️⃣  How to View Messages in Phoenix UI:")
    print()
    print("   Option A: View in Span Details")
    print("   -------------------------")
    print("   1. Open Phoenix UI: http://localhost:6006")
    print("   2. Click on a 'merchant_query' span")
    print("   3. Look for the 'Attributes' tab")
    print("   4. Find: input.value (user message)")
    print("   5. Find: output.value (assistant response)")
    print()
    print("   Option B: View in Span Events")
    print("   -------------------------")
    print("   1. Click on a span")
    print("   2. Go to 'Events' tab")
    print("   3. Look for 'user_message' event")
    print("      - message.role: user")
    print("      - message.content: <query text>")
    print("   4. Look for 'assistant_message' event")
    print("      - message.role: assistant")
    print("      - message.content: <response text>")
    print()
    print("   Option C: View LangChain Child Spans")
    print("   -------------------------")
    print("   1. Expand the 'merchant_query' span")
    print("   2. Look for child spans (ChatOpenAI, RunnableSequence, etc.)")
    print("   3. These should have llm.input_messages and llm.output_messages")
    print()

    # Common issues
    print("5️⃣  Common Issues & Fixes:")
    print()
    print("   Issue: All messages show 'undefined'")
    print("   Fix 1: Ensure Phoenix container is running")
    print("         → docker compose up -d")
    print("   Fix 2: Restart your application after starting Phoenix")
    print("   Fix 3: Check that traces are actually being sent")
    print("         → Look for 'Phoenix instrumentation enabled' message at startup")
    print()
    print("   Issue: No traces appear in Phoenix")
    print("   Fix 1: Check endpoint connectivity")
    print("         → curl http://localhost:4317")
    print("   Fix 2: Check Phoenix logs")
    print("         → docker compose logs phoenix")
    print("   Fix 3: Verify PHOENIX_ENABLED=true in environment")
    print()
    print("   Issue: Child spans don't show messages")
    print("   Fix: This is expected - messages are on parent 'merchant_query' span")
    print("        Look at the Attributes: input.value and output.value")
    print()

    # Test run suggestion
    print("6️⃣  Test Message Capture:")
    print()
    print("   Run this command to test message visibility:")
    print("   → uv run python examples/session_with_phoenix_tracing.py")
    print()
    print("   Then in Phoenix UI:")
    print("   1. Filter by: session.advisor_id = 'adv_demo_001'")
    print("   2. Click on first 'merchant_query' span")
    print("   3. Check Attributes tab for 'input.value' and 'output.value'")
    print("   4. Check Events tab for 'user_message' and 'assistant_message'")
    print()

    print("=" * 80)


def run_simple_test():
    """Run a simple test to verify message capture."""
    print("\n" + "=" * 80)
    print("SIMPLE MESSAGE CAPTURE TEST")
    print("=" * 80)
    print()

    if not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: OPENAI_API_KEY not set")
        print("  Please set it in .env file first")
        return

    print("Running a single query to test message capture...")
    print()

    try:
        from openai_langchain_deepagent.agent import (
            run_query_in_session,
            start_merchant_session,
        )

        # Start session
        agent, thread_id, state = start_merchant_session(
            advisor_id="test_advisor",
            merchant_id="test_merchant",
            merchant_name="Test Merchant",
        )

        print(f"✓ Session created: {state['session_id']}")
        print()

        # Run one query
        query = "What is 2+2?"
        print(f"Query: {query}")
        print()

        response, state = run_query_in_session(
            agent=agent, thread_id=thread_id, session_state=state, query=query
        )

        print(f"Response: {response[:100]}...")
        print()
        print("=" * 80)
        print("✓ Test Complete!")
        print("=" * 80)
        print()
        print("Now check Phoenix UI:")
        print(f"1. Filter by: session.id = '{state['session_id']}'")
        print("2. Click on the 'merchant_query' span")
        print("3. Look at Attributes tab:")
        print(f"   - input.value should be: '{query}'")
        print(f"   - output.value should contain the response")
        print()
        print("4. Look at Events tab:")
        print("   - user_message event with message.content")
        print("   - assistant_message event with message.content")
        print()

    except Exception as e:
        print(f"✗ Error running test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_phoenix_setup()

    response = input("\n🤔 Run a simple test query to verify message capture? (y/n): ")
    if response.lower() == "y":
        run_simple_test()
