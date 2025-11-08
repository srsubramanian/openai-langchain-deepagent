"""Tests for the agent module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from openai_langchain_deepagent.agent import create_agent


class TestCreateAgent:
    """Tests for create_agent function."""

    @patch("openai_langchain_deepagent.agent.ChatAnthropic")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_anthropic(self, mock_deep_agent, mock_chat_anthropic):
        """Test creating an agent with Anthropic provider."""
        # Mock environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            # Mock the LLM and DeepAgent
            mock_llm = MagicMock()
            mock_chat_anthropic.return_value = mock_llm
            mock_agent = MagicMock()
            mock_deep_agent.return_value = mock_agent

            # Create agent
            agent = create_agent(provider="anthropic")

            # Verify ChatAnthropic was called with correct parameters
            mock_chat_anthropic.assert_called_once()
            call_kwargs = mock_chat_anthropic.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["api_key"] == "test-key"

            # Verify DeepAgent was created with the LLM
            mock_deep_agent.assert_called_once_with(llm=mock_llm)
            assert agent == mock_agent

    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_openai(self, mock_deep_agent, mock_chat_openai):
        """Test creating an agent with OpenAI provider."""
        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock the LLM and DeepAgent
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_agent = MagicMock()
            mock_deep_agent.return_value = mock_agent

            # Create agent
            agent = create_agent(provider="openai")

            # Verify ChatOpenAI was called with correct parameters
            mock_chat_openai.assert_called_once()
            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["api_key"] == "test-key"

            # Verify DeepAgent was created with the LLM
            mock_deep_agent.assert_called_once_with(llm=mock_llm)
            assert agent == mock_agent

    @patch("openai_langchain_deepagent.agent.ChatAnthropic")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_custom_model(self, mock_deep_agent, mock_chat_anthropic):
        """Test creating an agent with custom model."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            mock_llm = MagicMock()
            mock_chat_anthropic.return_value = mock_llm

            create_agent(provider="anthropic", model="claude-3-opus-20240229")

            call_kwargs = mock_chat_anthropic.call_args[1]
            assert call_kwargs["model"] == "claude-3-opus-20240229"

    def test_create_agent_missing_anthropic_key(self):
        """Test that ValueError is raised when ANTHROPIC_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
                create_agent(provider="anthropic")

    def test_create_agent_missing_openai_key(self):
        """Test that ValueError is raised when OPENAI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                create_agent(provider="openai")

    def test_create_agent_unsupported_provider(self):
        """Test that ValueError is raised for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_agent(provider="invalid_provider")
