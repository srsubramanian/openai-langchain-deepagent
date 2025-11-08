"""Basic example of using a DeepAgent with OpenAI."""

from openai_langchain_deepagent.agent import run_agent_task


def main():
    """Run a simple DeepAgent example using OpenAI."""
    # Example 1: Simple coding task
    print("Example 1: Simple coding task")
    print("=" * 60)

    task = "Write a Python function that calculates the Fibonacci sequence up to n terms"
    result = run_agent_task(task)

    print(f"Task: {task}")
    print(f"\nResult:\n{result.get('output', result)}")
    print("\n" + "=" * 60 + "\n")

    # Example 2: Planning task
    print("Example 2: Planning task")
    print("=" * 60)

    task = (
        "Create a plan to build a simple REST API with Flask. "
        "Break it down into steps."
    )
    result = run_agent_task(task)

    print(f"Task: {task}")
    print(f"\nResult:\n{result.get('output', result)}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
