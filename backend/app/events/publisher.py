"""CloudEvents publisher utility for Phase V event-driven architecture.

Task: T-520 - Backend Event Publisher Utility
Phase: Phase V - Event-Driven Architecture

This module provides a reusable EventPublisher class that publishes CloudEvents
to an HTTP-based message broker using Dapr's pubsub API.

Dapr Pub/Sub API Endpoint:
    POST http://<dapr-host>:<dapr-http-port>/v1.0/publish/<pubsub-name>/<topic>

Example Usage:
    ```python
    from app.events.publisher import EventPublisher, get_event_publisher
    from app.events.schemas import TaskCreatedEvent, TaskCreatedData

    # Get publisher instance
    publisher = get_event_publisher()

    # Create event
    event = TaskCreatedEvent(
        source="/api/tasks",
        subject="task/123",
        data=TaskCreatedData(
            task_id=123,
            user_id=1,
            title="Buy groceries",
            description="Get milk and eggs",
            priority="medium"
        )
    )

    # Publish to topic
    await publisher.publish_task_event(event)
    ```
"""

import os
import httpx
import logging
from typing import Optional, Literal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.events.schemas import (
    CloudEvent,
    TaskCreatedEvent,
    TaskUpdatedEvent,
    TaskDeletedEvent,
    ReminderScheduledEvent,
    ReminderFiredEvent,
    NotificationSentEvent
)

# Configure logging
logger = logging.getLogger(__name__)

# Topic names for event routing
TASK_EVENTS_TOPIC = "task-events"
REMINDER_EVENTS_TOPIC = "reminder-events"
NOTIFICATION_EVENTS_TOPIC = "notification-events"


class EventPublisherError(Exception):
    """Base exception for event publishing errors."""
    pass


class EventPublisher:
    """CloudEvents publisher with HTTP-based Dapr pubsub support.

    This publisher sends CloudEvents to a Dapr sidecar via HTTP POST,
    which then routes events to the configured message broker (e.g., Kafka, Redis).

    Attributes:
        dapr_host: Dapr sidecar hostname (default: localhost)
        dapr_http_port: Dapr HTTP port (default: 3500)
        pubsub_name: Name of the Dapr pubsub component (default: todo-pubsub)
        max_retries: Maximum retry attempts for failed publishes (default: 3)
        enabled: Whether event publishing is enabled (default: False in dev)
    """

    def __init__(
        self,
        dapr_host: str = "localhost",
        dapr_http_port: int = 3500,
        pubsub_name: str = "todo-pubsub",
        max_retries: int = 3,
        enabled: bool = False,
        timeout: float = 5.0
    ):
        """Initialize EventPublisher.

        Args:
            dapr_host: Dapr sidecar hostname
            dapr_http_port: Dapr HTTP API port
            pubsub_name: Name of Dapr pubsub component
            max_retries: Maximum number of retry attempts
            enabled: Whether to actually publish events (False = no-op mode)
            timeout: HTTP request timeout in seconds
        """
        self.dapr_host = dapr_host
        self.dapr_http_port = dapr_http_port
        self.pubsub_name = pubsub_name
        self.max_retries = max_retries
        self.enabled = enabled
        self.timeout = timeout

        # Build base URL for Dapr pubsub API
        self.base_url = f"http://{dapr_host}:{dapr_http_port}/v1.0/publish/{pubsub_name}"

        # HTTP client for async requests
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(
            f"EventPublisher initialized: enabled={enabled}, "
            f"dapr_url={self.base_url}, max_retries={max_retries}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client instance.

        Returns:
            Async HTTP client for Dapr API calls
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("EventPublisher HTTP client closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _publish_event(self, topic: str, event: CloudEvent) -> bool:
        """Publish CloudEvent to specified topic with retry logic.

        This method implements exponential backoff retry for transient failures.
        Retries up to 3 times with exponential backoff (1s, 2s, 4s, ..., max 10s).

        Args:
            topic: Dapr pubsub topic name
            event: CloudEvent to publish

        Returns:
            True if publish succeeded, False otherwise

        Raises:
            EventPublisherError: If publish fails after all retries
        """
        if not self.enabled:
            logger.debug(
                f"Event publishing disabled (no-op mode). "
                f"Would publish {event.type} to {topic}"
            )
            return True

        try:
            # Build Dapr pubsub publish URL
            url = f"{self.base_url}/{topic}"

            # Serialize event to CloudEvents JSON format
            event_data = event.model_dump(mode="json")

            # Get HTTP client
            client = await self._get_client()

            # Publish event via HTTP POST
            logger.info(
                f"Publishing event {event.id} (type={event.type}) to topic={topic}"
            )

            response = await client.post(
                url,
                json=event_data,
                headers={
                    "Content-Type": "application/cloudevents+json",
                    "Ce-Id": event.id,
                    "Ce-Source": event.source,
                    "Ce-Type": event.type,
                    "Ce-Specversion": event.specversion
                }
            )

            # Check response status
            response.raise_for_status()

            logger.info(
                f"Successfully published event {event.id} to topic={topic}"
            )
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error publishing event {event.id} to {topic}: "
                f"status={e.response.status_code}, body={e.response.text}"
            )
            raise EventPublisherError(
                f"Failed to publish event: HTTP {e.response.status_code}"
            ) from e

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(
                f"Network error publishing event {event.id} to {topic}: {e}"
            )
            # Re-raise for retry mechanism
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error publishing event {event.id} to {topic}: {e}",
                exc_info=True
            )
            raise EventPublisherError(f"Unexpected publish error: {e}") from e

    async def publish_task_event(
        self,
        event: TaskCreatedEvent | TaskUpdatedEvent | TaskDeletedEvent
    ) -> bool:
        """Publish task-related event to task-events topic.

        Args:
            event: Task event (created, updated, or deleted)

        Returns:
            True if publish succeeded

        Raises:
            EventPublisherError: If publish fails after retries
        """
        return await self._publish_event(TASK_EVENTS_TOPIC, event)

    async def publish_reminder_event(
        self,
        event: ReminderScheduledEvent | ReminderFiredEvent
    ) -> bool:
        """Publish reminder-related event to reminder-events topic.

        Args:
            event: Reminder event (scheduled or fired)

        Returns:
            True if publish succeeded

        Raises:
            EventPublisherError: If publish fails after retries
        """
        return await self._publish_event(REMINDER_EVENTS_TOPIC, event)

    async def publish_notification_event(
        self,
        event: NotificationSentEvent
    ) -> bool:
        """Publish notification event to notification-events topic.

        Args:
            event: Notification sent event

        Returns:
            True if publish succeeded

        Raises:
            EventPublisherError: If publish fails after retries
        """
        return await self._publish_event(NOTIFICATION_EVENTS_TOPIC, event)

    async def publish(
        self,
        event: CloudEvent,
        topic: Optional[str] = None
    ) -> bool:
        """Generic publish method for any CloudEvent.

        Routes event to appropriate topic based on event type if topic not specified.

        Args:
            event: CloudEvent to publish
            topic: Optional explicit topic name (auto-detected if None)

        Returns:
            True if publish succeeded

        Raises:
            EventPublisherError: If publish fails after retries
        """
        # Auto-detect topic from event type if not specified
        if topic is None:
            topic = self._get_topic_for_event_type(event.type)

        return await self._publish_event(topic, event)

    def _get_topic_for_event_type(self, event_type: str) -> str:
        """Determine topic name based on event type.

        Args:
            event_type: CloudEvent type field (e.g., "task.created")

        Returns:
            Topic name for the event type
        """
        if event_type.startswith("task."):
            return TASK_EVENTS_TOPIC
        elif event_type.startswith("reminder."):
            return REMINDER_EVENTS_TOPIC
        elif event_type.startswith("notification."):
            return NOTIFICATION_EVENTS_TOPIC
        else:
            logger.warning(
                f"Unknown event type '{event_type}', defaulting to task-events topic"
            )
            return TASK_EVENTS_TOPIC


# ============================================================================
# Singleton instance and dependency injection
# ============================================================================

_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get or create EventPublisher singleton instance.

    Reads configuration from environment variables:
        - EVENT_PUBLISHING_ENABLED: Enable/disable event publishing (default: false)
        - DAPR_HOST: Dapr sidecar hostname (default: localhost)
        - DAPR_HTTP_PORT: Dapr HTTP port (default: 3500)
        - DAPR_PUBSUB_NAME: Dapr pubsub component name (default: todo-pubsub)
        - EVENT_PUBLISHER_MAX_RETRIES: Max retry attempts (default: 3)
        - EVENT_PUBLISHER_TIMEOUT: HTTP timeout in seconds (default: 5.0)

    Returns:
        EventPublisher singleton instance

    Example:
        ```python
        from app.events.publisher import get_event_publisher

        publisher = get_event_publisher()
        await publisher.publish_task_event(event)
        ```
    """
    global _event_publisher

    if _event_publisher is None:
        # Read configuration from environment
        enabled = os.getenv("EVENT_PUBLISHING_ENABLED", "false").lower() == "true"
        dapr_host = os.getenv("DAPR_HOST", "localhost")
        dapr_http_port = int(os.getenv("DAPR_HTTP_PORT", "3500"))
        pubsub_name = os.getenv("DAPR_PUBSUB_NAME", "todo-pubsub")
        max_retries = int(os.getenv("EVENT_PUBLISHER_MAX_RETRIES", "3"))
        timeout = float(os.getenv("EVENT_PUBLISHER_TIMEOUT", "5.0"))

        _event_publisher = EventPublisher(
            dapr_host=dapr_host,
            dapr_http_port=dapr_http_port,
            pubsub_name=pubsub_name,
            max_retries=max_retries,
            enabled=enabled,
            timeout=timeout
        )

    return _event_publisher


async def close_event_publisher():
    """Close EventPublisher singleton and cleanup resources.

    Should be called on application shutdown.

    Example:
        ```python
        from app.events.publisher import close_event_publisher

        @app.on_event("shutdown")
        async def shutdown():
            await close_event_publisher()
        ```
    """
    global _event_publisher

    if _event_publisher is not None:
        await _event_publisher.close()
        _event_publisher = None
