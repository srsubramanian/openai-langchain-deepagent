"""Tests for the main module."""

from openai_langchain_deepagent.main import hello


def test_hello_default():
    """Test hello function with default argument."""
    assert hello() == "Hello, World!"


def test_hello_custom_name():
    """Test hello function with custom name."""
    assert hello("Alice") == "Hello, Alice!"
