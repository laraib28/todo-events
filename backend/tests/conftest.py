"""Pytest configuration and shared fixtures."""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import User, Task, ConversationHistory
from app.auth import hash_password, create_jwt


# Use in-memory SQLite for testing
@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        name="Test User"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_token")
def auth_token_fixture(test_user: User) -> str:
    """Create a valid JWT token for test user."""
    return create_jwt(test_user.id)


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(auth_token: str) -> dict:
    """Create headers with auth cookie."""
    return {"Cookie": f"access_token={auth_token}"}


@pytest.fixture(name="test_task")
def test_task_fixture(session: Session, test_user: User) -> Task:
    """Create a test task."""
    task = Task(
        user_id=test_user.id,
        title="Test Task",
        description="Test Description",
        priority="medium",
        is_complete=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture(name="conversation_history")
def conversation_history_fixture(session: Session, test_user: User) -> list[ConversationHistory]:
    """Create test conversation history."""
    messages = [
        ConversationHistory(
            user_id=test_user.id,
            role="user",
            content="Hello"
        ),
        ConversationHistory(
            user_id=test_user.id,
            role="assistant",
            content="Hello! How can I help you with your tasks today?"
        ),
    ]
    for msg in messages:
        session.add(msg)
    session.commit()
    return messages


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "500")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.7")
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "10")
