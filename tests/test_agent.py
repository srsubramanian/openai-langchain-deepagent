"""Tests for the agent module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from openai_langchain_deepagent.agent import create_agent


class TestCreateAgent:
    """Tests for create_agent function."""

    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_default(self, mock_deep_agent, mock_chat_openai):
        """Test creating an agent with default parameters."""
        # Mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock the LLM and DeepAgent
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_agent = MagicMock()
            mock_deep_agent.return_value = mock_agent

            # Create agent
            agent = create_agent()

            # Verify ChatOpenAI was called with correct parameters
            mock_chat_openai.assert_called_once()
            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["api_key"] == "test-key"

            # Verify DeepAgent was created with the LLM
            mock_deep_agent.assert_called_once_with(llm=mock_llm)
            assert agent == mock_agent

    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_custom_model(self, mock_deep_agent, mock_chat_openai):
        """Test creating an agent with custom model."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            create_agent(model="gpt-4-turbo")

            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["model"] == "gpt-4-turbo"

    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.DeepAgent")
    def test_create_agent_custom_temperature(self, mock_deep_agent, mock_chat_openai):
        """Test creating an agent with custom temperature."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            create_agent(temperature=0.5)

            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["temperature"] == 0.5

    def test_create_agent_missing_api_key(self):
        """Test that ValueError is raised when OPENAI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                create_agent()
