"""Basic example of using a LangChain Agent with OpenAI."""

from openai_langchain_deepagent.agent import run_agent_task


def main():
    """Run a simple LangChain agent example using OpenAI."""
    # Example 1: Calculator task
    print("Example 1: Calculator task")
    print("=" * 60)

    task = "Calculate 123 * 456 using the calculator tool"
    result = run_agent_task(task)

    print(f"Task: {task}")
    print(f"\nResult:\n{result['messages'][-1].content if result.get('messages') else result}")
    print("\n" + "=" * 60 + "\n")

    # Example 2: General question
    print("Example 2: General question")
    print("=" * 60)

    task = "What is the capital of France?"
    result = run_agent_task(task)

    print(f"Task: {task}")
    print(f"\nResult:\n{result['messages'][-1].content if result.get('messages') else result}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
