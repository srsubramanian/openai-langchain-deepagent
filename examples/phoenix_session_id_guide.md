# Phoenix Session ID Guide: Where to Find Messages

## Understanding the Two ID Types

Your session uses **two different IDs**:

1. **`session.id`** - Layer 1 session identifier
   - Format: `ses_YYYYMMDD_HHMMSS_{uuid8}`
   - Example: `ses_20251109_121702_e42f2526`
   - Used for: Grouping all queries in a merchant conversation

2. **`session.thread_id`** - LangGraph checkpoint/thread identifier
   - Format: `merchant_{merchant_id}_{YYYYMMDD_HHMMSS}`
   - Example: `merchant_mch_789456_20251109_121606`
   - Used for: LangGraph conversation memory

## How to Find Messages by session.id

### Step 1: Filter by session.id
```
In Phoenix UI, add filter:
session.id = "ses_20251109_121702_e42f2526"
```

### Step 2: Look for "merchant_query" spans
You should see one or more spans with name: **`merchant_query`**

```
Timeline View:
└─ merchant_query [Query 1]    ← Click HERE
   ├─ RunnableSequence
   ├─ ChatOpenAI
   └─ ...other child spans
```

### Step 3: Click on the merchant_query span (NOT the child spans)

### Step 4: Check the Attributes tab
Scroll down to find:
- **`input.value`** ← User message HERE
- **`output.value`** ← AI response HERE

### Step 5: Check the Events tab (alternative view)
Look for these events:
- **`user_message`**
  - `message.role: user`
  - `message.content: <user query>`
- **`assistant_message`**
  - `message.role: assistant`
  - `message.content: <AI response>`

## Common Mistake: Looking at Child Spans

❌ **WRONG:** Clicking on child spans like:
- `RunnableSequence`
- `ChatOpenAI`
- `ChatPromptTemplate`

These child spans have different attributes (like `llm.input_messages`) but NOT `input.value`/`output.value`.

✅ **RIGHT:** Click on the **parent `merchant_query` span**

## How to Find Messages by thread_id

If you filter by thread_id instead:
```
session.thread_id = "merchant_mch_789456_20251109_121606"
```

You'll see the same `merchant_query` spans. Follow the same steps above.

## Visual Example

```
Phoenix UI after filtering by session.id:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Traces (filtered by session.id = "ses_20251109_121702_e42f2526")

📍 merchant_query                    ← CLICK HERE FOR MESSAGES
   Duration: 2.5s
   └─ Expand to see child spans

   Attributes:
   ├─ session.id: ses_20251109_121702_e42f2526
   ├─ session.thread_id: merchant_mch_789456_20251109_121606
   ├─ merchant.id: mch_789456
   ├─ session.query_number: 1
   ├─ input.value: "What are typical decline rates?"    ← USER MESSAGE
   └─ output.value: "Typical decline rates are..."      ← AI RESPONSE

   Events:
   ├─ user_message
   │  ├─ message.role: user
   │  └─ message.content: "What are typical decline rates?"
   ├─ assistant_message
   │  ├─ message.role: assistant
   │  └─ message.content: "Typical decline rates are..."
   └─ session_snapshot_before, session_snapshot_after
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quick Test

Run this to generate a test session:
```bash
uv run python examples/session_with_phoenix_tracing.py
```

After it runs, it will print:
```
Session ID: ses_20251109_143022_abc123de
Thread ID: merchant_mch_789456_20251109_143022
```

In Phoenix:
1. Filter: `session.id = "ses_20251109_143022_abc123de"`
2. You should see 4 `merchant_query` spans (4 queries in the demo)
3. Click on first `merchant_query` span
4. Go to **Attributes** tab
5. Find `input.value` and `output.value` - these are your messages!

## Still Showing "undefined"?

If you still see undefined:

### Check 1: Are you looking at the right span?
- Make sure you clicked on **`merchant_query`** (parent span)
- NOT on child spans like `RunnableSequence` or `ChatOpenAI`

### Check 2: Is the attribute spelled correctly?
- It's `input.value` (lowercase, with dot)
- NOT `Input.Value` or `input_value`

### Check 3: Scroll down in Attributes tab
- There are many attributes
- `input.value` and `output.value` might be near the bottom
- Use Ctrl+F to search for "input.value"

### Check 4: Try the Events tab instead
- Events tab is an alternative view
- Look for `user_message` and `assistant_message` events
- Expand them to see `message.content`

### Check 5: Check if tracing is enabled
Run: `uv run python examples/phoenix_message_troubleshooting.py`

This will verify your setup and run a test query.

## Need Help?

If messages are still showing as undefined after checking all the above:
1. Run the troubleshooting script
2. Check Phoenix container logs: `docker compose logs phoenix`
3. Verify Phoenix is running: `curl http://localhost:4317`
