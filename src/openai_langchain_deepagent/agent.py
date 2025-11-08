"""DeepAgent implementation using LangChain DeepAgents library."""

import os
from typing import Optional

from deepagents import DeepAgent
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


def create_agent(
    provider: str = "anthropic",
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> DeepAgent:
    """
    Create a DeepAgent with the specified LLM provider.

    Args:
        provider: LLM provider to use ("anthropic" or "openai")
        model: Specific model name. If None, uses defaults:
               - anthropic: claude-sonnet-4-5-20250929
               - openai: gpt-4o
        temperature: Temperature for the model (0.0-1.0)

    Returns:
        Configured DeepAgent instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
        llm = ChatAnthropic(
            model=model or "claude-sonnet-4-5-20250929",
            temperature=temperature,
            api_key=api_key,
        )
    elif provider == "openai":
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
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Choose 'anthropic' or 'openai'."
        )

    # Create and return the DeepAgent
    return DeepAgent(llm=llm)


def run_agent_task(task: str, provider: str = "anthropic") -> dict:
    """
    Run a task with a DeepAgent.

    Args:
        task: The task description for the agent to execute
        provider: LLM provider to use ("anthropic" or "openai")

    Returns:
        Dictionary containing the agent's response and execution details

    Example:
        >>> result = run_agent_task("Write a hello world function in Python")
        >>> print(result['output'])
    """
    agent = create_agent(provider=provider)

    # Execute the task
    result = agent.invoke({"task": task})

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
