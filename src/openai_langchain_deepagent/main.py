"""Main module for the application."""


def hello(name: str = "World") -> str:
    """
    Return a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"


def main() -> None:
    """Main entry point for the application."""
    print(hello())
    print("\n" + "=" * 60)
    print("LangChain Agents with OpenAI and Session Memory")
    print("=" * 60)
    print("\nThis project demonstrates LangChain Agents with OpenAI")
    print("featuring Layer 1 Session Memory for merchant conversations.")
    print("\nTo run examples:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your OPENAI_API_KEY")
    print("  3. Run: uv run python examples/basic_agent.py")
    print("\nFor more info, see: https://docs.langchain.com/oss/python/langchain/agents")
    print("=" * 60)


if __name__ == "__main__":
    main()
