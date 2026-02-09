#!/usr/bin/env python3
"""Reminder Worker Entry Point.

Task: T-523 - Reminder Service (Worker)
Phase: Phase V - Event-Driven Architecture

This script starts the ReminderWorker service as a standalone daemon.

Usage:
    python run_reminder_worker.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string (required)
    EVENT_PUBLISHING_ENABLED - Enable event publishing (default: false)
    DAPR_HOST - Dapr sidecar hostname (default: localhost)
    DAPR_HTTP_PORT - Dapr HTTP port (default: 3500)
    REMINDER_WORKER_POLL_INTERVAL - Poll interval in seconds (default: 30)
    REMINDER_WORKER_BATCH_SIZE - Max reminders per cycle (default: 100)
    REMINDER_WORKER_ENABLED - Enable/disable worker (default: true)

Example:
    # Run with default settings
    python run_reminder_worker.py

    # Run with custom poll interval
    REMINDER_WORKER_POLL_INTERVAL=60 python run_reminder_worker.py

    # Run with event publishing enabled (requires Dapr)
    EVENT_PUBLISHING_ENABLED=true python run_reminder_worker.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlmodel import Session, create_engine
from sqlalchemy.pool import NullPool

from app.workers.reminder_worker import ReminderWorker
from app.events.publisher import get_event_publisher

# Load environment variables
load_dotenv()


def main():
    """Main entry point for reminder worker."""
    # Check if worker is enabled
    worker_enabled = os.getenv("REMINDER_WORKER_ENABLED", "true").lower() == "true"
    if not worker_enabled:
        print("Reminder worker is disabled (REMINDER_WORKER_ENABLED=false)")
        sys.exit(0)

    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is required")
        sys.exit(1)

    poll_interval = int(os.getenv("REMINDER_WORKER_POLL_INTERVAL", "30"))
    batch_size = int(os.getenv("REMINDER_WORKER_BATCH_SIZE", "100"))

    print(f"Reminder Worker Configuration:")
    print(f"  Database: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")
    print(f"  Poll Interval: {poll_interval}s")
    print(f"  Batch Size: {batch_size}")
    print(f"  Event Publishing: {os.getenv('EVENT_PUBLISHING_ENABLED', 'false')}")
    print()

    # Create database engine
    # Use NullPool for worker to avoid connection pooling issues
    engine = create_engine(
        database_url,
        echo=False,
        poolclass=NullPool  # Worker doesn't need connection pooling
    )

    # Session factory
    def get_session() -> Session:
        return Session(engine)

    # Get event publisher (singleton)
    event_publisher = get_event_publisher()

    # Create and run worker
    worker = ReminderWorker(
        session_factory=get_session,
        event_publisher=event_publisher,
        poll_interval=poll_interval,
        batch_size=batch_size
    )

    # Run worker
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
