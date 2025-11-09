"""Tests for checkpointing and conversation memory."""

import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest

from openai_langchain_deepagent.agent import create_agent
from openai_langchain_deepagent.session_utils import (
    clear_all_sessions,
    clear_session,
    get_session_info,
    list_active_sessions,
)


class TestCheckpointing:
    """Tests for checkpointing functionality."""

    @patch("openai_langchain_deepagent.agent.create_deep_agent")
    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.SqliteSaver")
    def test_checkpointing_enabled(
        self, mock_sqlite_saver, mock_chat_openai, mock_create_deep_agent
    ):
        """Test that checkpointing can be enabled."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock the components
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_checkpointer = MagicMock()
            mock_sqlite_saver.from_conn_string.return_value = mock_checkpointer
            mock_agent = MagicMock()
            mock_create_deep_agent.return_value = mock_agent

            # Create agent with checkpointing enabled
            agent = create_agent(enable_checkpointing=True)

            # Verify checkpointer was created and passed
            mock_sqlite_saver.from_conn_string.assert_called_once_with(
                "checkpoints.db"
            )
            mock_create_deep_agent.assert_called_once_with(
                model=mock_llm, checkpointer=mock_checkpointer
            )

    @patch("openai_langchain_deepagent.agent.create_deep_agent")
    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    def test_checkpointing_disabled(self, mock_chat_openai, mock_create_deep_agent):
        """Test that checkpointing can be disabled."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock the components
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_agent = MagicMock()
            mock_create_deep_agent.return_value = mock_agent

            # Create agent with checkpointing disabled
            agent = create_agent(enable_checkpointing=False)

            # Verify checkpointer was NOT passed
            mock_create_deep_agent.assert_called_once_with(
                model=mock_llm, checkpointer=None
            )

    @patch("openai_langchain_deepagent.agent.create_deep_agent")
    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.SqliteSaver")
    def test_custom_checkpoint_path(
        self, mock_sqlite_saver, mock_chat_openai, mock_create_deep_agent
    ):
        """Test using a custom checkpoint database path."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock the components
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_checkpointer = MagicMock()
            mock_sqlite_saver.from_conn_string.return_value = mock_checkpointer
            mock_agent = MagicMock()
            mock_create_deep_agent.return_value = mock_agent

            # Create agent with custom checkpoint path
            custom_path = "custom_checkpoints.db"
            agent = create_agent(
                enable_checkpointing=True, checkpoint_db_path=custom_path
            )

            # Verify custom path was used
            mock_sqlite_saver.from_conn_string.assert_called_once_with(custom_path)


class TestSessionUtils:
    """Tests for session utility functions."""

    def setup_method(self):
        """Create a temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()

    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_session_utils_empty_db(self):
        """Test session utils with empty database."""
        # Should not crash with empty database
        sessions = list_active_sessions(self.db_path)
        assert sessions == []

        info = get_session_info("nonexistent", self.db_path)
        assert info is None

        deleted = clear_session("nonexistent", self.db_path)
        assert deleted == 0

    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        # Clear on empty database should not crash
        deleted = clear_all_sessions(self.db_path)
        assert deleted == 0


class TestConversationMemory:
    """Integration tests for conversation memory (requires mocking)."""

    @patch("openai_langchain_deepagent.agent.create_deep_agent")
    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.SqliteSaver")
    def test_multiple_sessions_isolated(
        self, mock_sqlite_saver, mock_chat_openai, mock_create_deep_agent
    ):
        """Test that different thread_ids maintain isolated sessions."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Mock components
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_checkpointer = MagicMock()
            mock_sqlite_saver.from_conn_string.return_value = mock_checkpointer

            # Create mock agent that tracks invocations
            invocations = []

            def mock_invoke(messages, config=None):
                invocations.append(
                    {"config": config, "message_count": len(messages.get("messages", []))}
                )
                return {"messages": [MagicMock(content="Response")]}

            mock_agent = MagicMock()
            mock_agent.invoke = mock_invoke
            mock_create_deep_agent.return_value = mock_agent

            # Create agent with checkpointing
            agent = create_agent(enable_checkpointing=True)

            # Invoke with different thread IDs
            thread1 = f"thread-{uuid.uuid4().hex[:8]}"
            thread2 = f"thread-{uuid.uuid4().hex[:8]}"

            agent.invoke(
                {"messages": [{"role": "user", "content": "Message 1"}]},
                config={"configurable": {"thread_id": thread1}},
            )

            agent.invoke(
                {"messages": [{"role": "user", "content": "Message 2"}]},
                config={"configurable": {"thread_id": thread2}},
            )

            # Verify different configs were used
            assert len(invocations) == 2
            assert invocations[0]["config"]["configurable"]["thread_id"] == thread1
            assert invocations[1]["config"]["configurable"]["thread_id"] == thread2

    @patch("openai_langchain_deepagent.agent.create_deep_agent")
    @patch("openai_langchain_deepagent.agent.ChatOpenAI")
    @patch("openai_langchain_deepagent.agent.SqliteSaver")
    def test_env_var_configuration(
        self, mock_sqlite_saver, mock_chat_openai, mock_create_deep_agent
    ):
        """Test that environment variables control checkpointing."""
        # Test with checkpointing enabled via env var
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "ENABLE_CHECKPOINTING": "true",
                "CHECKPOINT_DB_PATH": "test_checkpoints.db",
            },
        ):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm
            mock_checkpointer = MagicMock()
            mock_sqlite_saver.from_conn_string.return_value = mock_checkpointer
            mock_agent = MagicMock()
            mock_create_deep_agent.return_value = mock_agent

            # Create agent without explicit parameters
            agent = create_agent()

            # Verify checkpointer was created with env var path
            mock_sqlite_saver.from_conn_string.assert_called_once_with(
                "test_checkpoints.db"
            )
            mock_create_deep_agent.assert_called_once_with(
                model=mock_llm, checkpointer=mock_checkpointer
            )
