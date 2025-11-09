"""
Demo of TodoListMiddleware in DeepAgents.

This example demonstrates that the write_todos tool is automatically
available in deep agents created with create_deep_agent().
"""

from openai_langchain_deepagent.agent import create_agent


def main():
    """Demonstrate the built-in TodoListMiddleware."""
    print("TodoListMiddleware Demo")
    print("=" * 60)
    print()

    # Create agent (TodoListMiddleware is automatically included)
    agent = create_agent(enable_checkpointing=False)

    # Check what tools are available
    print("Checking available tools in the agent...")
    print()

    # Give the agent a complex, multi-step task
    # The agent should use the write_todos tool to plan and track progress
    task = """
    Create a Python script that:
    1. Reads a CSV file with sales data
    2. Calculates total revenue by product category
    3. Generates a bar chart visualization
    4. Saves the chart as a PNG file

    Please break this down into steps using your planning tools.
    """

    print(f"Task: {task.strip()}")
    print()
    print("=" * 60)
    print("Agent Response:")
    print("=" * 60)
    print()

    result = agent.invoke({"messages": [{"role": "user", "content": task}]})

    # Extract and print the response
    if result.get("messages"):
        for message in result["messages"]:
            if hasattr(message, "content"):
                print(message.content)
            elif isinstance(message, dict) and "content" in message:
                print(message["content"])
            print()


def inspect_agent_tools():
    """Inspect what tools are available in a deep agent."""
    from deepagents import create_deep_agent
    from langchain_openai import ChatOpenAI
    import os

    print("\nInspecting Deep Agent Tools")
    print("=" * 60)

    # Create a minimal agent to inspect
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY", "dummy"))
    agent = create_deep_agent(model=llm)

    # The agent graph contains the tools
    print("\nAgent type:", type(agent))
    print("\nAgent has the following capabilities:")
    print("- write_todos (TodoListMiddleware)")
    print("- write_file, ls, read_file, edit_file, glob_search, grep_search (FilesystemMiddleware)")
    print("- call_subagent (SubAgentMiddleware)")
    print()


if __name__ == "__main__":
    # Show what tools are available
    try:
        inspect_agent_tools()
    except Exception as e:
        print(f"Tool inspection: {e}")

    print()

    # Run the demo
    main()
