"""Demo: Layer 1 Session Memory with Phoenix Tracing.

This example demonstrates how multi-turn sessions are traced in Phoenix with:
- Session metadata on every span
- Session state snapshots before/after each query
- Cache hit/miss tracking
- Complete session lifecycle visibility

Prerequisites:
- Phoenix running: docker-compose up -d
- Phoenix UI: http://localhost:6006
- OPENAI_API_KEY set in .env
"""

import json
import os
import sys
import time

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
    cache_data,
    get_cached_data,
)

# Import OpenTelemetry for parent span
try:
    from opentelemetry import trace

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    print("⚠️  OpenTelemetry not available - traces will not be sent to Phoenix")


def demo_traced_multi_turn_session():
    """
    Demo: Complete multi-turn session with Phoenix tracing.

    Shows how to view multi-turn conversations in Phoenix with full context.
    """
    print("=" * 80)
    print("PHOENIX TRACING DEMO: Multi-Turn Session with Full Observability")
    print("=" * 80)
    print()

    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set it in your .env file")
        sys.exit(1)

    print("📊 Phoenix should be running at: http://localhost:6006")
    print("   Open Phoenix UI to see traces in real-time!")
    print()
    print("🔍 What to look for in Phoenix:")
    print("   - Filter by session.thread_id to see all queries in this session")
    print("   - View 'session_snapshot_before' and 'session_snapshot_after' events")
    print("   - Check cache.hit attributes on cache_lookup spans")
    print("   - Track session evolution via session.topics and session.recommendations_count")
    print()
    input("Press ENTER to start the demo...")
    print()

    # Create parent span for entire session lifecycle
    if TRACING_AVAILABLE:
        tracer = trace.get_tracer(__name__)
        parent_span = tracer.start_span("merchant_session_lifecycle")
    else:
        parent_span = None

    try:
        # ====================================================================
        # PART 1: Session Initialization
        # ====================================================================
        print("=" * 80)
        print("PART 1: Starting Session")
        print("=" * 80)

        agent, thread_id, state = start_merchant_session(
            advisor_id="adv_demo_001",
            merchant_id="789456",
            merchant_name="TechRetail Co",
            segment="mid_market",
        )

        if parent_span:
            parent_span.set_attribute("session.thread_id", thread_id)
            parent_span.set_attribute("merchant.id", state["merchant_id"])
            parent_span.add_event("session_started")

        print(f"✅ Session Started")
        print(f"   Thread ID (session identifier): {thread_id}")
        print(f"   Merchant: {state['merchant_id']} ({state['merchant_name']})")
        print(f"   Segment: {state['segment']}")
        print()

        # ====================================================================
        # PART 2: First Query - No Cache
        # ====================================================================
        print("=" * 80)
        print("PART 2: Query 1 - Initial Question (No Cache)")
        print("=" * 80)

        query1 = "What are typical decline rates for mid-market retail merchants?"
        print(f"🗣️  Query: {query1}")
        print()

        response, state = run_query_in_session(
            agent=agent, thread_id=thread_id, session_state=state, query=query1
        )

        print(f"🤖 Response: {response[:150]}...")
        print()

        # Add topic and cache some data
        state = add_topic(state, "decline_rates")
        state = cache_data(
            state,
            "profile",
            {
                "merchant_name": "TechRetail Co",
                "industry": "Retail",
                "avg_transaction": 45.00,
            },
        )
        print("✅ Added topic: decline_rates")
        print("✅ Cached merchant profile data")
        print()

        print(
            f"📊 Phoenix: Look for span 'merchant_query' with session.query_number=1"
        )
        print(
            f"   Check 'session_snapshot_before' (queries=0) and 'session_snapshot_after' (queries=1)"
        )
        print()
        time.sleep(2)  # Give time to view in Phoenix

        # ====================================================================
        # PART 3: Second Query - Cache Hit
        # ====================================================================
        print("=" * 80)
        print("PART 3: Query 2 - Follow-up Question (Cache Hit Expected)")
        print("=" * 80)

        query2 = "What strategies can reduce decline rates?"
        print(f"🗣️  Query: {query2}")
        print()

        # Demonstrate cache lookup BEFORE query
        print("🔍 Checking cache for 'profile' data...")
        cached_profile = get_cached_data(state, "profile")
        if cached_profile:
            print(f"   ✅ Cache HIT: {cached_profile}")
        else:
            print("   ❌ Cache MISS")
        print()

        response, state = run_query_in_session(
            agent=agent, thread_id=thread_id, session_state=state, query=query2
        )

        print(f"🤖 Response: {response[:150]}...")
        print()

        # Add recommendation
        state = add_recommendation(
            state=state,
            recommendation_type="decline_optimization",
            priority="high",
            description="Review fraud filter settings - may be too aggressive",
            expected_impact="Could reduce false positives by 15-20%",
        )
        print("✅ Added recommendation: Review fraud filter settings")
        print()

        print(
            f"📊 Phoenix: Look for 'cache_lookup' span with cache.hit=true for 'profile'"
        )
        print(f"   Session snapshot should show: topics_count=1, recommendations_count=1")
        print()
        time.sleep(2)

        # ====================================================================
        # PART 4: Third Query - Tests Conversation Memory
        # ====================================================================
        print("=" * 80)
        print("PART 4: Query 3 - Reference Previous Context (Memory Test)")
        print("=" * 80)

        query3 = "Can you summarize what we just discussed about decline rates?"
        print(f"🗣️  Query: {query3}")
        print("   (This tests if agent remembers previous conversation)")
        print()

        response, state = run_query_in_session(
            agent=agent, thread_id=thread_id, session_state=state, query=query3
        )

        print(f"🤖 Response: {response[:200]}...")
        print()

        state = add_advisor_note(
            state, "Merchant is interested in decline rate optimization strategies"
        )
        print("✅ Added advisor note")
        print()

        print(f"📊 Phoenix: Query 3 should reference context from Query 1 and 2")
        print(
            f"   All 3 queries should have same session.thread_id: {thread_id}"
        )
        print()
        time.sleep(2)

        # ====================================================================
        # PART 5: Fourth Query - Cache Metrics
        # ====================================================================
        print("=" * 80)
        print("PART 4: Query 4 - Cache Metrics with Different TTL")
        print("=" * 80)

        # Cache metrics data (shorter TTL - 5 minutes vs 30 minutes for profile)
        state = cache_data(
            state, "metrics", {"decline_rate": 3.2, "approval_rate": 96.8}
        )
        print("✅ Cached metrics data (TTL: 5 minutes)")
        print()

        query4 = "What other metrics should I monitor?"
        print(f"🗣️  Query: {query4}")
        print()

        response, state = run_query_in_session(
            agent=agent, thread_id=thread_id, session_state=state, query=query4
        )

        print(f"🤖 Response: {response[:150]}...")
        print()

        state = add_topic(state, "metrics_monitoring")
        print("✅ Added topic: metrics_monitoring")
        print()

        print(f"📊 Phoenix: Should see 2 different cache entries with different TTLs")
        print(
            f"   profile: cache_age_profile={state.get('cached_at', {}).get('profile', 'N/A')}"
        )
        print(
            f"   metrics: cache_age_metrics={state.get('cached_at', {}).get('metrics', 'N/A')}"
        )
        print()
        time.sleep(2)

        # ====================================================================
        # PART 6: Session Summary
        # ====================================================================
        print("=" * 80)
        print("PART 6: Session Summary")
        print("=" * 80)

        if parent_span:
            parent_span.set_attribute("session.final_query_count", state["total_queries"])
            parent_span.add_event("session_completed")

        # Print detailed session state
        print_session_state(state, detailed=True)

        # Export summary
        summary = export_session_summary(state)
        print("\n📄 Session Summary (JSON):")
        print(json.dumps(summary, indent=2))
        print()

        # ====================================================================
        # PART 7: Phoenix Analysis Instructions
        # ====================================================================
        print("=" * 80)
        print("PHOENIX ANALYSIS GUIDE")
        print("=" * 80)
        print()
        print("🔍 How to analyze this session in Phoenix:")
        print()
        print("1️⃣  View All Queries in Session:")
        print(f'   Filter: session.thread_id = "{thread_id}"')
        print("   Sort by: timestamp")
        print("   You should see 4 'merchant_query' spans")
        print()
        print("2️⃣  Track Session Evolution:")
        print("   Click on any 'merchant_query' span")
        print("   Look for Events: 'session_snapshot_before' and 'session_snapshot_after'")
        print("   Watch how topics_count and recommendations_count change")
        print()
        print("3️⃣  Analyze Cache Performance:")
        print("   Filter: cache.data_type = profile")
        print("   Check: cache.hit = true/false")
        print("   View: cache.age_seconds vs cache.ttl_seconds")
        print()
        print("4️⃣  Group by Merchant:")
        print(f'   Filter: merchant.id = "{state["merchant_id"]}"')
        print("   Shows all sessions for this merchant")
        print()
        print("5️⃣  Find Sessions with Recommendations:")
        print("   Filter: session.recommendations_count > 0")
        print(f"   Group by: advisor.id")
        print()
        print("6️⃣  Track Query Patterns:")
        print("   View: query.text attributes")
        print("   Analyze: response.length over time")
        print()

        print("=" * 80)
        print("✅ Demo Complete!")
        print("=" * 80)
        print()
        print("💡 Next Steps:")
        print("   1. Open Phoenix UI: http://localhost:6006")
        print(f'   2. Filter by: session.thread_id = "{thread_id}"')
        print("   3. Explore traces, events, and attributes")
        print("   4. Try filtering by merchant.id, advisor.id, or cache.hit")
        print()

    finally:
        if parent_span:
            parent_span.end()


def demo_cache_expiration_tracing():
    """
    Demo: Cache expiration tracking in Phoenix.

    Shows how cache TTL and expiration are traced.
    """
    print("\n\n")
    print("=" * 80)
    print("BONUS DEMO: Cache Expiration Tracing")
    print("=" * 80)
    print()

    agent, thread_id, state = start_merchant_session(
        advisor_id="adv_cache_demo", merchant_id="111222", merchant_name="CacheTest"
    )

    print(f"Thread ID (session identifier): {thread_id}")
    print()

    # Cache data
    state = cache_data(state, "transactions", {"count": 150, "total": 15000.0})
    print("✅ Cached 'transactions' data (TTL: 60 seconds)")
    print()

    # Immediate lookup - should hit
    print("🔍 Lookup 1: Immediate (should HIT)")
    data = get_cached_data(state, "transactions")
    print(f"   Result: {'HIT' if data else 'MISS'}")
    print()

    # Lookup after 5 seconds - should still hit
    print("⏱️  Waiting 5 seconds...")
    time.sleep(5)
    print("🔍 Lookup 2: After 5 seconds (should HIT)")
    data = get_cached_data(state, "transactions")
    print(f"   Result: {'HIT' if data else 'MISS'}")
    print()

    print("📊 Phoenix: Check 'cache_lookup' spans")
    print("   First lookup: cache.hit=true, cache.age_seconds ≈ 0")
    print("   Second lookup: cache.hit=true, cache.age_seconds ≈ 5")
    print("   Both should show cache.ttl_seconds = 60")
    print()

    print("💡 To see cache MISS, wait 60+ seconds and lookup again!")
    print()


if __name__ == "__main__":
    # Run main demo
    demo_traced_multi_turn_session()

    # Optional: Run cache expiration demo
    response = input("\n🤔 Run cache expiration demo? (y/n): ")
    if response.lower() == "y":
        demo_cache_expiration_tracing()
