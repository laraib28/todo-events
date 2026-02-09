"""Tests for chat endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from openai import RateLimitError, APIConnectionError, APIError

from app.models import User, ConversationHistory
from app.schemas import ChatRequest, ChatResponse


class TestChatEndpoint:
    """Test suite for POST /api/chat endpoint."""

    def test_chat_endpoint_exists(self, client: TestClient):
        """Test that the chat endpoint exists and requires authentication."""
        response = client.post("/api/chat", json={"message": "Hello"})
        # Should return 401 without auth, not 404
        assert response.status_code in [401, 422]

    def test_chat_requires_authentication(self, client: TestClient):
        """Test that chat endpoint requires JWT authentication."""
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 401
        assert "authenticated" in response.json()["detail"].lower()

    def test_chat_validates_request_schema(self, client: TestClient, auth_headers: dict):
        """Test that chat validates ChatRequest schema."""
        # Empty message
        response = client.post("/api/chat", json={"message": ""}, headers=auth_headers)
        assert response.status_code == 422

        # Missing message field
        response = client.post("/api/chat", json={}, headers=auth_headers)
        assert response.status_code == 422

        # Message too long (> 2000 chars)
        long_message = "a" * 2001
        response = client.post("/api/chat", json={"message": long_message}, headers=auth_headers)
        assert response.status_code == 422

    def test_chat_validates_whitespace_only_message(self, client: TestClient, auth_headers: dict):
        """Test that whitespace-only messages are rejected."""
        response = client.post("/api/chat", json={"message": "   "}, headers=auth_headers)
        assert response.status_code == 422

    @patch('app.routers.chat.TodoAgent')
    def test_chat_successful_response(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_headers: dict
    ):
        """Test successful chat response with no tool call."""
        # Mock agent response
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "Hello! How can I help you?",
            "metadata": None
        })
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Hello! How can I help you?"
        assert data.get("metadata") is None

        # Verify agent was called with correct parameters
        mock_agent.process_message.assert_called_once()
        call_args = mock_agent.process_message.call_args
        assert call_args.kwargs["user_id"] == test_user.id
        assert call_args.kwargs["user_message"] == "Hello"

    @patch('app.routers.chat.TodoAgent')
    def test_chat_with_task_creation_metadata(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test chat response with task creation metadata."""
        # Mock agent response with metadata
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "I've created a new task: 'Buy milk' with high priority.",
            "metadata": {
                "action": "task_created",
                "task_id": 42
            }
        })
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Add buy milk with high priority"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "I've created a new task: 'Buy milk' with high priority."
        assert data["metadata"] is not None
        assert data["metadata"]["action"] == "task_created"
        assert data["metadata"]["task_id"] == 42

    @patch('app.routers.chat.TodoAgent')
    def test_chat_with_task_listing_metadata(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test chat response with task listing metadata."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "You have 5 tasks.",
            "metadata": {
                "action": "tasks_listed",
                "count": 5
            }
        })
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Show my tasks"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["action"] == "tasks_listed"
        assert data["metadata"]["count"] == 5

    def test_ai_prompt_includes_fuzzy_matching_rules(self):
        """Ensure system prompt enforces list-before-not-found and fuzzy/partial matching rules."""
        from app.ai.prompts import SYSTEM_PROMPT

        assert "ALWAYS call list_tasks() BEFORE deciding a task is missing" in SYSTEM_PROMPT
        assert "Match case-insensitively" in SYSTEM_PROMPT
        assert "partial/substring matching" in SYSTEM_PROMPT
        assert "Only report \"not found\" AFTER calling list_tasks()" in SYSTEM_PROMPT
        assert "Prefer updating existing tasks" in SYSTEM_PROMPT

    @patch('app.routers.chat.TodoAgent')
    def test_chat_handles_openai_rate_limit(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that OpenAI rate limit errors return 429."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=None, body=None)
        )
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()

    @patch('app.routers.chat.TodoAgent')
    def test_chat_handles_openai_connection_error(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that OpenAI connection errors return 503."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(
            side_effect=APIConnectionError(request=None)
        )
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 503
        assert "connect" in response.json()["detail"].lower()

    @patch('app.routers.chat.TodoAgent')
    def test_chat_handles_openai_api_error(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that OpenAI API errors return 500."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(
            side_effect=APIError("API Error", request=None, body=None)
        )
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 500
        assert "api error" in response.json()["detail"].lower()

    @patch('app.routers.chat.TodoAgent')
    def test_chat_handles_generic_exception(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that generic exceptions return 500."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()

    @patch('app.routers.chat.TodoAgent')
    def test_chat_stores_conversation_in_db(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_headers: dict
    ):
        """Test that conversation messages are stored (verified via agent call)."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "Response",
            "metadata": None
        })
        mock_agent_class.return_value = mock_agent

        client.post(
            "/api/chat",
            json={"message": "Test message"},
            headers=auth_headers
        )

        # Verify agent was called with database session
        call_args = mock_agent.process_message.call_args
        assert "session" in call_args.kwargs
        assert call_args.kwargs["user_message"] == "Test message"

    def test_chat_enforces_user_isolation(
        self,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_headers: dict
    ):
        """Test that users can only access their own conversations."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            name="Other User"
        )
        session.add(other_user)
        session.commit()

        # Create conversation for other user
        other_msg = ConversationHistory(
            user_id=other_user.id,
            role="user",
            content="Other user's message"
        )
        session.add(other_msg)
        session.commit()

        # Test user makes a request - should only see their own history
        # (This is verified internally by the agent loading only test_user's history)
        with patch('app.routers.chat.TodoAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.process_message = AsyncMock(return_value={
                "message": "Response",
                "metadata": None
            })
            mock_agent_class.return_value = mock_agent

            client.post(
                "/api/chat",
                json={"message": "My message"},
                headers=auth_headers
            )

            # Verify agent was called with test_user's ID, not other_user's ID
            call_args = mock_agent.process_message.call_args
            assert call_args.kwargs["user_id"] == test_user.id
            assert call_args.kwargs["user_id"] != other_user.id

    @patch('app.routers.chat.TodoAgent')
    def test_chat_response_schema_validation(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that response conforms to ChatResponse schema."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "Test response",
            "metadata": {
                "action": "task_created",
                "task_id": 1
            }
        })
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "Test"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "message" in data
        assert isinstance(data["message"], str)

        # Verify optional metadata structure
        if data.get("metadata"):
            assert "action" in data["metadata"]
            assert data["metadata"]["action"] in [
                "task_created", "task_updated", "task_deleted",
                "task_completed", "task_uncompleted", "tasks_listed", "no_action"
            ]

    def test_chat_invalid_auth_token(self, client: TestClient):
        """Test that invalid JWT tokens are rejected."""
        invalid_headers = {"Cookie": "access_token=invalid.token.here"}
        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=invalid_headers
        )
        assert response.status_code == 401

    @patch('app.routers.chat.TodoAgent')
    def test_chat_message_trimming(
        self,
        mock_agent_class: MagicMock,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that whitespace is trimmed from messages."""
        mock_agent = MagicMock()
        mock_agent.process_message = AsyncMock(return_value={
            "message": "Response",
            "metadata": None
        })
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/chat",
            json={"message": "  Hello  "},
            headers=auth_headers
        )

        assert response.status_code == 200
        # Verify trimmed message was passed to agent
        call_args = mock_agent.process_message.call_args
        assert call_args.kwargs["user_message"] == "Hello"
