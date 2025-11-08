"""DeepAgent implementation using LangChain DeepAgents library with OpenAI."""

import os
from typing import Any, Optional

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


def create_agent(
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> Any:
    """
    Create a DeepAgent with OpenAI.

    Args:
        model: Specific model name. If None, uses default: gpt-4o
        temperature: Temperature for the model (0.0-1.0)

    Returns:
        Configured deep agent instance

    Raises:
        ValueError: If OPENAI_API_KEY is missing
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )

    llm = ChatOpenAI(
        model=model or "gpt-4o",
        temperature=temperature,
        api_key=api_key,
    )

    # Create and return the deep agent
    return create_deep_agent(llm=llm)


def run_agent_task(task: str, model: Optional[str] = None) -> dict:
    """
    Run a task with a DeepAgent using OpenAI.

    Args:
        task: The task description for the agent to execute
        model: Optional specific model to use (default: gpt-4o)

    Returns:
        Dictionary containing the agent's response and execution details

    Example:
        >>> result = run_agent_task("Write a hello world function in Python")
        >>> print(result['output'])
    """
    agent = create_agent(model=model)

    # Execute the task
    result = agent.invoke({"messages": [{"role": "user", "content": task}]})

    return result


if __name__ == "__main__":
    # Example usage
    example_task = "Create a simple Python function that adds two numbers"

    print(f"Running task: {example_task}\n")
    print("=" * 60)

    result = run_agent_task(example_task)

    print("\nAgent Response:")
    print("=" * 60)
    print(result.get("output", result))
