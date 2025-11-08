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
    print("LangChain DeepAgents Integration")
    print("=" * 60)
    print("\nThis project demonstrates LangChain DeepAgents capabilities.")
    print("\nTo run examples:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your API keys (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
    print("  3. Run: uv run python examples/basic_agent.py")
    print("\nFor more info, see: https://docs.langchain.com/oss/python/deepagents/overview")
    print("=" * 60)


if __name__ == "__main__":
    main()
