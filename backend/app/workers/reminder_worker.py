"""Reminder Worker Service for processing due reminders.

Task: T-523 - Reminder Service (Worker)
Phase: Phase V - Event-Driven Architecture

This worker service polls the reminders table for due reminders and:
1. Publishes reminder.fired CloudEvents
2. Updates reminder status to 'fired'
3. Logs processing metrics

The worker runs as a continuous daemon with configurable polling interval.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Callable, Optional
from sqlmodel import Session, select

from app.models import Reminder
from app.events.publisher import EventPublisher
from app.events.schemas import TaskReminderFiredEvent, TaskReminderFiredData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReminderWorker:
    """Worker service that processes due reminders.

    This worker polls the database for reminders where:
    - status = 'pending'
    - scheduled_time <= NOW()

    For each due reminder:
    1. Publishes reminder.fired event via EventPublisher
    2. Updates status to 'fired' and sets fired_at timestamp
    3. Commits transaction

    Event publishing is best-effort (failures don't block DB updates).
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        event_publisher: EventPublisher,
        poll_interval: int = 30,
        batch_size: int = 100
    ):
        """Initialize ReminderWorker.

        Args:
            session_factory: Callable that returns a database Session
            event_publisher: EventPublisher instance for publishing events
            poll_interval: Seconds between poll cycles (default: 30)
            batch_size: Max reminders to process per cycle (default: 100)
        """
        self.session_factory = session_factory
        self.event_publisher = event_publisher
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"ReminderWorker initialized "
            f"(poll_interval={poll_interval}s, batch_size={batch_size})"
        )

    async def process_due_reminders(self) -> int:
        """Process all due reminders (one batch).

        Queries database for pending reminders with scheduled_time <= NOW(),
        publishes reminder.fired events, and updates status to 'fired'.

        Returns:
            Number of reminders processed successfully

        Raises:
            Exception: If database query or connection fails
        """
        processed_count = 0
        failed_count = 0
        start_time = datetime.utcnow()

        try:
            # Create database session
            with self.session_factory() as session:
                # Query for due reminders
                statement = (
                    select(Reminder)
                    .where(Reminder.status == "pending")
                    .where(Reminder.scheduled_time <= datetime.utcnow())
                    .order_by(Reminder.scheduled_time.asc())
                    .limit(self.batch_size)
                )
                due_reminders = session.exec(statement).all()

                if not due_reminders:
                    logger.debug("No due reminders found")
                    return 0

                logger.info(f"Processing cycle started (found {len(due_reminders)} due reminders)")

                # Process each reminder
                for reminder in due_reminders:
                    try:
                        # Publish reminder.fired event
                        await self._publish_reminder_fired(reminder)

                        # Update reminder status
                        reminder.status = "fired"
                        reminder.fired_at = datetime.utcnow()
                        session.add(reminder)
                        session.commit()

                        processed_count += 1
                        logger.debug(
                            f"Fired reminder {reminder.id} for task {reminder.task_id} "
                            f"(scheduled: {reminder.scheduled_time})"
                        )

                    except Exception as e:
                        session.rollback()
                        failed_count += 1
                        logger.error(
                            f"Failed to process reminder {reminder.id}: {e}",
                            exc_info=True
                        )

        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            raise

        # Log processing summary
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Processing cycle complete "
            f"(fired: {processed_count}, failed: {failed_count}, duration: {duration:.2f}s)"
        )

        return processed_count

    async def _publish_reminder_fired(self, reminder: Reminder) -> None:
        """Publish reminder.fired event for a reminder.

        Best-effort publishing: Logs errors but doesn't raise exceptions.

        Args:
            reminder: Reminder instance to publish event for
        """
        try:
            # Extract notification channels from JSONB
            channels = ["email"]
            if isinstance(reminder.notification_channels, dict):
                channels = reminder.notification_channels.get("channels", ["email"])
            elif isinstance(reminder.notification_channels, list):
                channels = reminder.notification_channels

            # Create reminder.fired event
            event = TaskReminderFiredEvent(
                source="/workers/reminder-worker",
                subject=f"reminder/{reminder.id}",
                data=TaskReminderFiredData(
                    reminder_id=reminder.id,
                    task_id=int(str(reminder.task_id)),  # Convert UUID to int (temporary)
                    user_id=int(str(reminder.user_id)),  # Convert UUID to int (temporary)
                    fired_at=datetime.utcnow(),
                    scheduled_time=reminder.scheduled_time,
                    notification_channels=channels
                )
            )

            # Publish event (best-effort)
            await self.event_publisher.publish_reminder_event(event)
            logger.debug(f"Published reminder.fired event for reminder {reminder.id}")

        except Exception as e:
            # Log error but don't raise - reminder should still be marked as fired
            logger.warning(
                f"Failed to publish reminder.fired event for reminder {reminder.id}: {e}"
            )

    async def run(self) -> None:
        """Run the reminder worker main loop.

        Continuously polls for due reminders at configured interval.
        Handles graceful shutdown on SIGINT/SIGTERM.

        Raises:
            Exception: If unhandled exception occurs during processing
        """
        self._running = True
        logger.info("Reminder worker started")

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating graceful shutdown...")
            self._running = False
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self._running:
                try:
                    # Process due reminders
                    await self.process_due_reminders()

                except Exception as e:
                    # Log error but continue running
                    logger.error(f"Error processing reminders: {e}", exc_info=True)

                # Wait for next poll cycle (or shutdown signal)
                if self._running:
                    logger.info(f"Next poll in {self.poll_interval} seconds")
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.poll_interval
                        )
                    except asyncio.TimeoutError:
                        # Normal timeout, continue to next cycle
                        pass

        finally:
            # Cleanup on shutdown
            logger.info("Shutting down reminder worker...")
            await self.event_publisher.close()
            logger.info("Reminder worker stopped")

    def stop(self) -> None:
        """Request graceful shutdown of the worker.

        Sets the shutdown event to interrupt the sleep between poll cycles.
        """
        logger.info("Stop requested")
        self._running = False
        self._shutdown_event.set()
