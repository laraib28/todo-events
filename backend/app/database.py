"""Database connection and session management."""

import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine with connection pooling for Neon serverless
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL logging for development
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
)


def get_session():
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
