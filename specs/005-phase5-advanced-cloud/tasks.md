# Tasks: Phase V - Advanced Cloud Deployment with Event-Driven Architecture

**Input**: Design documents from `/specs/005-phase5-advanced-cloud/`

**Prerequisites**:
- `specs/005-phase5-advanced-cloud/plan.md` (architecture and design)
- `speckit.specify` (Phase V specification)
- Phase I-IV completed ✅

**Tests**: Unit tests, integration tests, end-to-end tests required. Validation via automated scripts.

**Organization**: Tasks organized into 12 phases aligned with plan.md architecture. Each phase has a clear goal and checkpoint.

---

## Format: `- [ ] T-5## [P?] [US#] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US#]**: Derived user story grouping for Phase V
- Every task includes concrete file path(s) to create/modify
- Dependencies marked explicitly

---

## Path Conventions

**Services**:
- `services/reminder/` - Reminder Service
- `services/notification/` - Notification Service
- `services/audit/` - Audit Service
- `services/recurring/` - Recurring Task Generator

**Backend Extensions**:
- `backend/app/` - Extended Backend API
- `backend/alembic/versions/` - Database migrations
- `backend/app/events/` - Event schemas and publishers

**Dapr**:
- `k8s/dapr-components/` - Dapr component configurations
- `k8s/dapr-install.sh` - Dapr installation script

**Kafka**:
- `k8s/kafka/` - Kafka deployment configs

**Helm**:
- `helm/todo-app/` - Updated Helm chart with Phase V services

**CI/CD**:
- `.github/workflows/` - GitHub Actions workflows

**Documentation**:
- `specs/005-phase5-advanced-cloud/` - Phase V documentation

---

## Derived User Stories for Phase V

- **US1**: Database schema extended for reminders, recurring tasks, and events
- **US2**: Event-driven architecture with Kafka and Dapr operational
- **US3**: Reminder service schedules and fires reminders accurately
- **US4**: Notification service sends multi-channel notifications
- **US5**: Audit service persists all events for compliance
- **US6**: Recurring task generator creates task instances daily
- **US7**: Backend API extended with new endpoints (reminders, recurring patterns)
- **US8**: Frontend UI supports due dates, reminders, and recurring patterns
- **US9**: Local (Minikube) deployment with all Phase V services
- **US10**: Cloud (production) deployment with HA and monitoring
- **US11**: CI/CD pipeline automates build, test, and deployment
- **US12**: System validated and production-ready

---

## Phase 1: Database Migrations and Schema Extensions (US1)

**Goal**: Extend PostgreSQL database with 5 new tables and extend tasks table for Phase V features.

**Plan Reference**: Data Architecture section

**Independent Test**:
- Run migration: `alembic upgrade head`
- Verify tables exist: `psql -c "\dt"`
- Check constraints: `psql -c "\d+ tasks"`

**Dependencies**: None (foundation phase)

### Migration Setup

- [ ] T-501 [P] [US1] Create backend/alembic/versions/003_phase5_event_driven.py migration file skeleton
- [ ] T-502 [US1] Add tasks table extensions in migration: due_date, reminder_time, reminder_config (JSONB), recurrence_pattern_id, recurrence_instance_id, is_recurring columns
- [ ] T-503 [US1] Add indexes in migration: idx_tasks_due_date, idx_tasks_recurrence_pattern

### New Tables

- [ ] T-504 [US1] Create recurrence_patterns table in migration with columns: id, user_id, task_template (JSONB), frequency, interval, days_of_week, day_of_month, end_date, max_occurrences, timezone, last_generated_at, created_at, updated_at
- [ ] T-505 [US1] Add recurrence_patterns constraints in migration: CHECK frequency IN (...), CHECK interval > 0, CHECK end_date OR max_occurrences (not both)
- [ ] T-506 [US1] Add recurrence_patterns indexes in migration: idx_recurrence_user, idx_recurrence_last_generated

- [ ] T-507 [P] [US1] Create reminders table in migration with columns: id, task_id, user_id, scheduled_time, status, notification_channels (JSONB), created_at, fired_at
- [ ] T-508 [P] [US1] Add reminders constraints in migration: CHECK status IN ('pending', 'fired', 'cancelled')
- [ ] T-509 [P] [US1] Add reminders indexes in migration: idx_reminders_task, idx_reminders_user, idx_reminders_scheduled (WHERE status='pending'), idx_reminders_status

- [ ] T-510 [P] [US1] Create events table in migration with columns: id, event_type, aggregate_id, user_id, payload (JSONB), metadata (JSONB), created_at, version
- [ ] T-511 [P] [US1] Add events indexes in migration: idx_events_type, idx_events_aggregate, idx_events_user, idx_events_created

- [ ] T-512 [P] [US1] Create notifications table in migration with columns: id, user_id, reminder_id, channel, recipient, subject, body, status, error_message, sent_at, created_at
- [ ] T-513 [P] [US1] Add notifications constraints in migration: CHECK channel IN ('email', 'in_app', 'webhook'), CHECK status IN ('pending', 'sent', 'failed')
- [ ] T-514 [P] [US1] Add notifications indexes in migration: idx_notifications_user, idx_notifications_status, idx_notifications_created

### Migration Testing

- [ ] T-515 [US1] Add downgrade logic in migration (reverse all table creations and alterations)
- [ ] T-516 [US1] Test migration upgrade on local database and record output in specs/005-phase5-advanced-cloud/migration-report.md
- [ ] T-517 [US1] Test migration downgrade and re-upgrade (verify idempotency) and record output in specs/005-phase5-advanced-cloud/migration-report.md
- [ ] T-518 [US1] Verify all indexes created successfully and record query plan samples in specs/005-phase5-advanced-cloud/migration-report.md

**Checkpoint**: Database schema extended, migration tested locally ✅

**Dependencies for Next Phase**: Migration file ready (used by all services)

---

## Phase 2: Event Schemas and Models (US2)

**Goal**: Define CloudEvents-compliant event schemas, create Python models for events, and implement event publishing utilities.

**Plan Reference**: Event-Driven Architecture section

**Independent Test**:
- Validate event schema against CloudEvents spec
- Unit test event creation and serialization

**Dependencies**: T-501 to T-518 (database models needed)

### Event Schema Definitions

- [ ] T-519 [P] [US2] Create backend/app/events/__init__.py package file
- [ ] T-520 [P] [US2] Create backend/app/events/schemas.py with CloudEvent base class (specversion, type, source, id, time, datacontenttype, data)
- [ ] T-521 [US2] Add TaskCreatedEvent schema in schemas.py with data payload (task_id, user_id, title, description, priority, due_date, reminder_time, is_recurring, created_at)
- [ ] T-522 [P] [US2] Add TaskUpdatedEvent schema in schemas.py with data payload (task_id, user_id, changes, updated_at)
- [ ] T-523 [P] [US2] Add TaskCompletedEvent schema in schemas.py with data payload (task_id, user_id, completed_at)
- [ ] T-524 [P] [US2] Add TaskDeletedEvent schema in schemas.py with data payload (task_id, user_id, deleted_at)
- [ ] T-525 [P] [US2] Add ReminderScheduledEvent schema in schemas.py with data payload (reminder_id, task_id, user_id, scheduled_time, notification_channels)
- [ ] T-526 [P] [US2] Add ReminderFiredEvent schema in schemas.py with data payload (reminder_id, task_id, user_id, task_title, due_date, notification_channels, scheduled_time, fired_at)
- [ ] T-527 [P] [US2] Add ReminderCancelledEvent schema in schemas.py with data payload (reminder_id, task_id, user_id, cancelled_at)
- [ ] T-528 [P] [US2] Add RecurringInstanceGeneratedEvent schema in schemas.py with data payload (task_id, user_id, recurrence_pattern_id, instance_date, generated_at)

### SQLModel Extensions

- [ ] T-529 [US2] Extend backend/app/models.py Task model with new columns: due_date, reminder_time, reminder_config, recurrence_pattern_id, recurrence_instance_id, is_recurring
- [ ] T-530 [P] [US2] Create RecurrencePattern model in backend/app/models.py with all fields from migration
- [ ] T-531 [P] [US2] Create Reminder model in backend/app/models.py with all fields from migration
- [ ] T-532 [P] [US2] Create Event model in backend/app/models.py with all fields from migration (for Audit Service)
- [ ] T-533 [P] [US2] Create Notification model in backend/app/models.py with all fields from migration (for Notification Service)

### Event Publisher Utility

- [ ] T-534 [US2] Create backend/app/events/publisher.py with DaprEventPublisher class (publish_event method using httpx to call Dapr HTTP API)
- [ ] T-535 [US2] Add DAPR_HTTP_PORT environment variable configuration in publisher.py (default: 3500)
- [ ] T-536 [US2] Add error handling and retry logic in publisher.py (exponential backoff, max 3 retries)
- [ ] T-537 [US2] Add logging for all event publications in publisher.py (include event type, correlation ID)

### Event Publisher Tests

- [ ] T-538 [P] [US2] Create backend/tests/test_events.py with unit tests for event schema validation (CloudEvents spec compliance)
- [ ] T-539 [P] [US2] Add unit tests for DaprEventPublisher (mock httpx, verify HTTP calls to Dapr)
- [ ] T-540 [P] [US2] Add integration test for event publishing (test against local Dapr sidecar or mock)

**Checkpoint**: Event schemas defined, publisher utility ready ✅

**Dependencies for Next Phase**: Event publisher used by Backend API and services

---

## Phase 3: Infrastructure Setup - Kafka and Dapr (US2)

**Goal**: Deploy Kafka cluster and Dapr runtime to both Minikube (local) and prepare for cloud deployment.

**Plan Reference**: Kafka Topic Design, Dapr Integration sections

**Independent Test**:
- Kafka: `kubectl exec -it kafka-0 -- kafka-topics.sh --list --bootstrap-server localhost:9092`
- Dapr: `dapr status -k`

**Dependencies**: Minikube running (Phase IV prerequisite)

### Kafka Setup (Local - Minikube)

- [ ] T-541 [US2] Create k8s/kafka/namespace.yaml for Kafka resources
- [ ] T-542 [US2] Create k8s/kafka/values-local.yaml for Bitnami Kafka Helm chart (replicaCount: 1, persistence: false)
- [ ] T-543 [US2] Create k8s/kafka/install-kafka-local.sh script to install Kafka via Helm with values-local.yaml
- [ ] T-544 [US2] Create k8s/kafka/create-topics.sh script to create 8 Kafka topics (tasks.task.created, tasks.task.updated, etc.) with retention policy 7 days
- [ ] T-545 [US2] Execute install-kafka-local.sh and record output in specs/005-phase5-advanced-cloud/kafka-install-report.md
- [ ] T-546 [US2] Execute create-topics.sh and verify topics created (kafka-topics.sh --list) and record output in specs/005-phase5-advanced-cloud/kafka-install-report.md
- [ ] T-547 [US2] Test Kafka producer/consumer with test message and record output in specs/005-phase5-advanced-cloud/kafka-test-report.md

### Kafka Setup (Cloud - Production)

- [ ] T-548 [P] [US2] Create k8s/kafka/values-production.yaml for production Kafka (replicaCount: 3, persistence: true, SASL/SSL enabled)
- [ ] T-549 [P] [US2] Document Confluent Cloud setup steps in specs/005-phase5-advanced-cloud/kafka-cloud-setup.md (alternative to self-hosted)
- [ ] T-550 [P] [US2] Create k8s/kafka/install-kafka-production.sh script for cloud Kafka deployment (Strimzi Operator or managed service)

### Dapr Setup (Local - Minikube)

- [ ] T-551 [US2] Create k8s/dapr-install.sh script to install Dapr control plane via Helm (namespace: dapr-system)
- [ ] T-552 [US2] Create k8s/dapr-components/pubsub-redis.yaml for local PubSub component (type: pubsub.redis)
- [ ] T-553 [US2] Create k8s/dapr-components/install-components-local.sh script to apply Redis PubSub component
- [ ] T-554 [US2] Install Redis via Helm (bitnami/redis) in todo-app namespace for Dapr PubSub backend
- [ ] T-555 [US2] Execute dapr-install.sh and verify Dapr control plane running (dapr status -k) and record output in specs/005-phase5-advanced-cloud/dapr-install-report.md
- [ ] T-556 [US2] Execute install-components-local.sh and verify component created (kubectl get components -n todo-app) and record output in specs/005-phase5-advanced-cloud/dapr-install-report.md

### Dapr Setup (Cloud - Production)

- [ ] T-557 [P] [US2] Create k8s/dapr-components/pubsub-kafka.yaml for production PubSub component (type: pubsub.kafka with SASL/SSL)
- [ ] T-558 [P] [US2] Create k8s/dapr-components/install-components-production.sh script to apply Kafka PubSub component
- [ ] T-559 [P] [US2] Document Dapr tracing configuration in specs/005-phase5-advanced-cloud/dapr-observability.md (Zipkin/Jaeger integration)

### Dapr Testing

- [ ] T-560 [US2] Create test publisher app (simple Python script) that publishes test event via Dapr and record output in specs/005-phase5-advanced-cloud/dapr-test-report.md
- [ ] T-561 [US2] Create test subscriber app (simple Python script) that subscribes to test topic via Dapr and record output in specs/005-phase5-advanced-cloud/dapr-test-report.md
- [ ] T-562 [US2] Deploy test apps to Minikube with Dapr annotations and verify end-to-end event flow (publish → Kafka → consume)

**Checkpoint**: Kafka and Dapr operational on Minikube, cloud configs ready ✅

**Dependencies for Next Phase**: Dapr PubSub component available for services

---

## Phase 4: Backend API Extensions (US7)

**Goal**: Extend existing Backend API with event publishing, recurring patterns endpoints, and reminders endpoints.

**Plan Reference**: Service 1: Backend API section

**Independent Test**:
- Create task with reminder: `POST /api/tasks` with due_date and reminder_time
- Verify event published to Kafka
- Create recurring pattern: `POST /api/tasks/recurring`

**Dependencies**: T-519 to T-540 (event schemas), T-541 to T-562 (Dapr available)

### Event Publishing Integration

- [ ] T-563 [US7] Extend backend/app/main.py to initialize DaprEventPublisher as singleton (dependency injection)
- [ ] T-564 [US7] Update POST /api/tasks endpoint in backend/app/routers/tasks.py to publish tasks.task.created event after task creation
- [ ] T-565 [US7] Update PUT /api/tasks/{id} endpoint to publish tasks.task.updated event after task update
- [ ] T-566 [US7] Update PATCH /api/tasks/{id}/toggle endpoint to publish tasks.task.completed event when task marked complete
- [ ] T-567 [US7] Update DELETE /api/tasks/{id} endpoint to publish tasks.task.deleted event after task deletion
- [ ] T-568 [US7] Add error handling for event publishing failures (log error but don't fail request)

### Recurring Patterns Endpoints

- [ ] T-569 [US7] Create backend/app/schemas.py RecurrencePatternCreate schema with validation (frequency, interval, task_template)
- [ ] T-570 [US7] Create backend/app/schemas.py RecurrencePatternResponse schema
- [ ] T-571 [US7] Create POST /api/tasks/recurring endpoint in backend/app/routers/tasks.py to create recurrence pattern
- [ ] T-572 [US7] Create GET /api/tasks/recurring endpoint to list user's recurrence patterns (user isolation via user_id)
- [ ] T-573 [US7] Create GET /api/tasks/recurring/{id} endpoint to get single recurrence pattern (verify ownership)
- [ ] T-574 [US7] Create PUT /api/tasks/recurring/{id} endpoint to update recurrence pattern
- [ ] T-575 [US7] Create DELETE /api/tasks/recurring/{id} endpoint to delete recurrence pattern (cascade delete future instances or mark inactive)

### Reminders Endpoints

- [ ] T-576 [P] [US7] Create backend/app/schemas.py ReminderCreate schema with validation
- [ ] T-577 [P] [US7] Create backend/app/schemas.py ReminderResponse schema
- [ ] T-578 [US7] Create POST /api/tasks/{id}/reminders endpoint in backend/app/routers/tasks.py to create reminder for task
- [ ] T-579 [US7] Create GET /api/tasks/{id}/reminders endpoint to list reminders for task
- [ ] T-580 [US7] Create DELETE /api/reminders/{id} endpoint to cancel reminder (update status to 'cancelled', publish reminder.cancelled event)

### Backend API Testing

- [ ] T-581 [P] [US7] Create backend/tests/test_recurring_patterns.py with unit tests for recurring pattern endpoints (CRUD operations)
- [ ] T-582 [P] [US7] Create backend/tests/test_reminders.py with unit tests for reminder endpoints
- [ ] T-583 [US7] Add integration tests for event publishing in backend/tests/test_events_integration.py (verify events reach Kafka)
- [ ] T-584 [US7] Update backend/app/main.py to add Dapr sidecar annotations readiness in health check

### Deployment Configuration

- [ ] T-585 [US7] Update backend/Dockerfile to include new dependencies (httpx for Dapr)
- [ ] T-586 [US7] Update backend/requirements.txt with httpx, tenacity (for retries)
- [ ] T-587 [US7] Add DAPR_HTTP_PORT environment variable to backend/.env.example (default: 3500)

**Checkpoint**: Backend API extended with event publishing and new endpoints ✅

**Dependencies for Next Phase**: Backend API publishes events (consumed by services)

---

## Phase 5: Reminder Service Implementation (US3)

**Goal**: Create standalone Reminder Service that schedules and fires reminders using APScheduler.

**Plan Reference**: Service 2: Reminder Service section, ADR-005-004

**Independent Test**:
- Deploy Reminder Service to Minikube
- Create task with reminder via API
- Verify reminder scheduled in APScheduler
- Wait for reminder to fire, verify event published

**Dependencies**: T-519 to T-562 (events and Dapr), T-563 to T-587 (Backend API publishes events)

### Service Setup

- [ ] T-588 [US3] Create services/reminder/ directory structure: app/, tests/, Dockerfile, requirements.txt
- [ ] T-589 [P] [US3] Create services/reminder/requirements.txt with FastAPI, APScheduler, SQLAlchemy, httpx, python-dateutil
- [ ] T-590 [P] [US3] Create services/reminder/Dockerfile (Python 3.11 slim, multi-stage build)
- [ ] T-591 [P] [US3] Create services/reminder/.dockerignore (tests/, __pycache__, .env)

### APScheduler Configuration

- [ ] T-592 [US3] Create services/reminder/app/scheduler.py with APScheduler setup (PostgreSQL JobStore, BackgroundScheduler)
- [ ] T-593 [US3] Configure APScheduler jobstore in scheduler.py (connection to PostgreSQL, table: apscheduler_jobs)
- [ ] T-594 [US3] Add timezone-aware scheduling support in scheduler.py (use pytz, UTC default)
- [ ] T-595 [US3] Add error handling for APScheduler in scheduler.py (misfire grace time: 60 seconds)

### Event Handlers (Dapr Subscribers)

- [ ] T-596 [US3] Create services/reminder/app/main.py with FastAPI app and Dapr subscription endpoint (/dapr/subscribe)
- [ ] T-597 [US3] Implement /dapr/subscribe endpoint to return subscription config (topics: tasks.task.created, tasks.task.updated, tasks.task.deleted)
- [ ] T-598 [US3] Create services/reminder/app/handlers.py with handle_task_created function (subscribe to tasks.task.created)
- [ ] T-599 [US3] Implement reminder scheduling logic in handle_task_created: extract reminder_time, schedule APScheduler job, save reminder to DB, publish reminder.scheduled event
- [ ] T-600 [US3] Create handle_task_updated function in handlers.py (update or cancel reminder if reminder_time changed)
- [ ] T-601 [US3] Create handle_task_deleted function in handlers.py (cancel pending reminders, update status to 'cancelled')

### Reminder Execution

- [ ] T-602 [US3] Create services/reminder/app/executor.py with fire_reminder function (called by APScheduler when job triggers)
- [ ] T-603 [US3] Implement fire_reminder logic: fetch reminder from DB, publish reminders.reminder.fired event via Dapr, update reminder status to 'fired', record fired_at timestamp
- [ ] T-604 [US3] Add error handling in fire_reminder (retry on failure, log errors, mark reminder as failed if retries exhausted)

### Database Access

- [ ] T-605 [P] [US3] Create services/reminder/app/database.py with PostgreSQL connection (shared with Backend API database)
- [ ] T-606 [P] [US3] Create services/reminder/app/models.py with Reminder SQLModel (reuse from backend or copy)
- [ ] T-607 [US3] Add database session management in main.py (dependency injection for handlers)

### Health Checks

- [ ] T-608 [US3] Create /health endpoint in main.py (check FastAPI is running)
- [ ] T-609 [US3] Create /ready endpoint in main.py (check database connection and APScheduler running)
- [ ] T-610 [US3] Add APScheduler health check (verify scheduler is running, no thread deadlocks)

### Testing

- [ ] T-611 [P] [US3] Create services/reminder/tests/test_scheduler.py with unit tests for APScheduler job creation
- [ ] T-612 [P] [US3] Create services/reminder/tests/test_handlers.py with unit tests for event handlers (mock Dapr, mock DB)
- [ ] T-613 [P] [US3] Create services/reminder/tests/test_executor.py with unit tests for fire_reminder function
- [ ] T-614 [US3] Create integration test for end-to-end reminder flow (schedule → fire → event published)

### Deployment Configuration

- [ ] T-615 [US3] Create k8s/deployment-reminder-service.yaml with Deployment (1 replica, Dapr annotations, resource limits)
- [ ] T-616 [US3] Add Dapr annotations in deployment: dapr.io/enabled: "true", dapr.io/app-id: "reminder-service", dapr.io/app-port: "8001"
- [ ] T-617 [US3] Create k8s/service-reminder-service.yaml (ClusterIP, port 8001, internal only)
- [ ] T-618 [US3] Add environment variables in deployment: DATABASE_URL, DAPR_HTTP_PORT
- [ ] T-619 [US3] Add liveness and readiness probes in deployment (GET /health, GET /ready)

**Checkpoint**: Reminder Service deployed, schedules and fires reminders ✅

**Dependencies for Next Phase**: Reminder Service publishes reminder.fired events (consumed by Notification Service)

---

## Phase 6: Notification Service Implementation (US4)

**Goal**: Create Notification Service that sends notifications via email, in-app, and webhook channels.

**Plan Reference**: Service 4: Notification Service section, ADR-005-006

**Independent Test**:
- Deploy Notification Service to Minikube
- Publish test reminder.fired event
- Verify email sent via SendGrid (sandbox mode)

**Dependencies**: T-519 to T-562 (events and Dapr), T-588 to T-619 (Reminder Service publishes events)

### Service Setup

- [ ] T-620 [US4] Create services/notification/ directory structure: app/, tests/, templates/email/, Dockerfile, requirements.txt
- [ ] T-621 [P] [US4] Create services/notification/requirements.txt with FastAPI, httpx, Jinja2, tenacity, sendgrid
- [ ] T-622 [P] [US4] Create services/notification/Dockerfile (Python 3.11 slim, multi-stage build)
- [ ] T-623 [P] [US4] Create services/notification/.dockerignore (tests/, __pycache__, .env)

### Event Handlers (Dapr Subscribers)

- [ ] T-624 [US4] Create services/notification/app/main.py with FastAPI app and Dapr subscription endpoint (/dapr/subscribe)
- [ ] T-625 [US4] Implement /dapr/subscribe endpoint to return subscription config (topic: reminders.reminder.fired)
- [ ] T-626 [US4] Create services/notification/app/handlers.py with handle_reminder_fired function
- [ ] T-627 [US4] Implement handler logic: extract notification channels from event, route to appropriate channel handler

### Channel Handlers

- [ ] T-628 [US4] Create services/notification/app/channels/__init__.py package
- [ ] T-629 [US4] Create services/notification/app/channels/email.py with EmailHandler class
- [ ] T-630 [US4] Implement EmailHandler.send method: render email template, call SendGrid API, handle errors with retries
- [ ] T-631 [US4] Add SendGrid API key configuration from environment variable (SENDGRID_API_KEY)
- [ ] T-632 [P] [US4] Create services/notification/app/channels/webhook.py with WebhookHandler class
- [ ] T-633 [P] [US4] Implement WebhookHandler.send method: HTTP POST to user's webhook URL with event payload
- [ ] T-634 [P] [US4] Create services/notification/app/channels/inapp.py with InAppHandler class (placeholder for future WebSocket implementation)

### Email Templates

- [ ] T-635 [P] [US4] Create services/notification/templates/email/base.html with base email layout (HTML structure, styles)
- [ ] T-636 [US4] Create services/notification/templates/email/reminder.html extending base.html with reminder notification content (task title, due date, CTA)
- [ ] T-637 [US4] Create services/notification/app/templates.py with template rendering logic using Jinja2

### Notification History

- [ ] T-638 [US4] Create services/notification/app/database.py with PostgreSQL connection
- [ ] T-639 [US4] Create services/notification/app/models.py with Notification SQLModel
- [ ] T-640 [US4] Add notification history persistence in channel handlers (save notification record before sending, update status after sending)

### Error Handling and Retries

- [ ] T-641 [US4] Add retry logic using tenacity in EmailHandler (3 attempts, exponential backoff)
- [ ] T-642 [US4] Add retry logic in WebhookHandler (3 attempts, exponential backoff)
- [ ] T-643 [US4] Add error logging for failed notifications (include error_message in notification record)

### Health Checks

- [ ] T-644 [P] [US4] Create /health endpoint in main.py
- [ ] T-645 [P] [US4] Create /ready endpoint in main.py (check database connection and SendGrid API connectivity)

### Testing

- [ ] T-646 [P] [US4] Create services/notification/tests/test_handlers.py with unit tests for event handlers
- [ ] T-647 [P] [US4] Create services/notification/tests/test_channels.py with unit tests for channel handlers (mock SendGrid API, mock webhook HTTP calls)
- [ ] T-648 [P] [US4] Create services/notification/tests/test_templates.py with unit tests for template rendering
- [ ] T-649 [US4] Create integration test for end-to-end notification flow (receive event → send email → verify sent)

### Deployment Configuration

- [ ] T-650 [US4] Create k8s/deployment-notification-service.yaml with Deployment (2 replicas, Dapr annotations, resource limits)
- [ ] T-651 [US4] Add Dapr annotations in deployment: dapr.io/enabled: "true", dapr.io/app-id: "notification-service", dapr.io/app-port: "8002"
- [ ] T-652 [US4] Create k8s/service-notification-service.yaml (ClusterIP, port 8002, internal only)
- [ ] T-653 [US4] Add environment variables in deployment: DATABASE_URL, DAPR_HTTP_PORT, SENDGRID_API_KEY (from Secret)
- [ ] T-654 [US4] Create k8s/secret-notification.yaml template for SendGrid API key (user must populate)
- [ ] T-655 [US4] Add liveness and readiness probes in deployment (GET /health, GET /ready)

**Checkpoint**: Notification Service deployed, sends email notifications ✅

**Dependencies for Next Phase**: Notification Service operational (independent of other new services)

---

## Phase 7: Audit Service Implementation (US5)

**Goal**: Create Audit Service that persists all events to PostgreSQL for compliance and debugging.

**Plan Reference**: Service 5: Audit Service section, ADR-005-007

**Independent Test**:
- Deploy Audit Service to Minikube
- Publish test event
- Verify event persisted in events table

**Dependencies**: T-519 to T-562 (events and Dapr)

### Service Setup

- [ ] T-656 [US5] Create services/audit/ directory structure: app/, tests/, Dockerfile, requirements.txt
- [ ] T-657 [P] [US5] Create services/audit/requirements.txt with FastAPI, SQLAlchemy, httpx
- [ ] T-658 [P] [US5] Create services/audit/Dockerfile (Python 3.11 slim, multi-stage build)
- [ ] T-659 [P] [US5] Create services/audit/.dockerignore (tests/, __pycache__, .env)

### Event Handlers (Dapr Subscribers)

- [ ] T-660 [US5] Create services/audit/app/main.py with FastAPI app and Dapr subscription endpoint (/dapr/subscribe)
- [ ] T-661 [US5] Implement /dapr/subscribe endpoint to return subscription config (topics: tasks.*, reminders.*, recurring.*)
- [ ] T-662 [US5] Create services/audit/app/handlers.py with handle_event function (generic handler for all events)
- [ ] T-663 [US5] Implement event persistence logic: extract event data, insert into events table, return success

### Database Access

- [ ] T-664 [P] [US5] Create services/audit/app/database.py with PostgreSQL connection
- [ ] T-665 [P] [US5] Create services/audit/app/models.py with Event SQLModel
- [ ] T-666 [US5] Add bulk insert optimization in handlers.py (buffer 100 events before batch insert for performance)

### Optional Query API

- [ ] T-667 [P] [US5] Create GET /api/audit/events endpoint in main.py to query events (filter by user_id, event_type, date range)
- [ ] T-668 [P] [US5] Create GET /api/audit/events/{id} endpoint to get single event by ID
- [ ] T-669 [P] [US5] Add pagination support in query endpoint (limit, offset parameters)

### Retention Policy

- [ ] T-670 [US5] Create services/audit/app/cleanup.py with delete_old_events function (delete events older than 90 days)
- [ ] T-671 [US5] Add cleanup job to be run weekly (document in deployment or create separate CronJob)

### Health Checks

- [ ] T-672 [P] [US5] Create /health endpoint in main.py
- [ ] T-673 [P] [US5] Create /ready endpoint in main.py (check database connection)

### Testing

- [ ] T-674 [P] [US5] Create services/audit/tests/test_handlers.py with unit tests for event persistence
- [ ] T-675 [P] [US5] Create services/audit/tests/test_query_api.py with unit tests for query endpoints
- [ ] T-676 [US5] Create integration test for end-to-end event persistence (publish event → verify in DB)

### Deployment Configuration

- [ ] T-677 [US5] Create k8s/deployment-audit-service.yaml with Deployment (1 replica, Dapr annotations, resource limits)
- [ ] T-678 [US5] Add Dapr annotations in deployment: dapr.io/enabled: "true", dapr.io/app-id: "audit-service", dapr.io/app-port: "8003"
- [ ] T-679 [US5] Create k8s/service-audit-service.yaml (ClusterIP, port 8003, internal only)
- [ ] T-680 [US5] Add environment variables in deployment: DATABASE_URL, DAPR_HTTP_PORT
- [ ] T-681 [US5] Add liveness and readiness probes in deployment (GET /health, GET /ready)

**Checkpoint**: Audit Service deployed, persists all events ✅

**Dependencies for Next Phase**: Audit Service operational (independent of other new services)

---

## Phase 8: Recurring Task Generator Implementation (US6)

**Goal**: Create Recurring Task Generator as Kubernetes CronJob that generates task instances daily.

**Plan Reference**: Service 3: Recurring Task Generator section, ADR-005-005

**Independent Test**:
- Create recurring pattern via API
- Manually trigger CronJob
- Verify task instances created in tasks table
- Verify recurring.instance.generated events published

**Dependencies**: T-563 to T-587 (Backend API with recurring patterns endpoints), T-519 to T-562 (Dapr)

### Service Setup

- [ ] T-682 [US6] Create services/recurring/ directory structure: app/, tests/, Dockerfile, requirements.txt
- [ ] T-683 [P] [US6] Create services/recurring/requirements.txt with SQLAlchemy, httpx, python-dateutil
- [ ] T-684 [P] [US6] Create services/recurring/Dockerfile (Python 3.11 slim, single-stage for batch job)
- [ ] T-685 [P] [US6] Create services/recurring/.dockerignore (tests/, __pycache__, .env)

### Generation Logic

- [ ] T-686 [US6] Create services/recurring/app/main.py with main() entry point (command-line script, not FastAPI)
- [ ] T-687 [US6] Create services/recurring/app/generator.py with RecurringTaskGenerator class
- [ ] T-688 [US6] Implement query_patterns method in generator.py (query recurrence_patterns where last_generated_at < today or NULL)
- [ ] T-689 [US6] Implement calculate_instances method in generator.py (calculate next 30 days of instances based on frequency, interval, days_of_week)
- [ ] T-690 [US6] Add recurrence pattern parsing logic (daily, weekly, monthly, yearly, custom)
- [ ] T-691 [US6] Add timezone-aware date calculations (use pytz, respect pattern timezone)

### Task Creation and Event Publishing

- [ ] T-692 [US6] Implement create_instances method in generator.py (bulk insert task instances to tasks table)
- [ ] T-693 [US6] Add instance deduplication logic (check recurrence_instance_id to avoid duplicate instances)
- [ ] T-694 [US6] Implement publish_events method in generator.py (publish recurring.instance.generated event for each instance via Dapr)
- [ ] T-695 [US6] Add batch event publishing (publish in batches of 100 to avoid overwhelming Kafka)

### Pattern Updates

- [ ] T-696 [US6] Implement update_patterns method in generator.py (update last_generated_at timestamp on patterns)
- [ ] T-697 [US6] Add end condition checking (end_date, max_occurrences) and mark patterns as inactive when complete

### Database Access

- [ ] T-698 [P] [US6] Create services/recurring/app/database.py with PostgreSQL connection
- [ ] T-699 [P] [US6] Create services/recurring/app/models.py with RecurrencePattern and Task SQLModels

### Logging and Error Handling

- [ ] T-700 [US6] Add comprehensive logging in main.py (log patterns processed, instances created, events published)
- [ ] T-701 [US6] Add error handling for database failures (rollback transaction, log error, exit with non-zero code)
- [ ] T-702 [US6] Add error handling for Dapr failures (log error but don't fail job, events will be republished next run)

### Testing

- [ ] T-703 [P] [US6] Create services/recurring/tests/test_generator.py with unit tests for pattern calculations (daily, weekly, monthly)
- [ ] T-704 [P] [US6] Create services/recurring/tests/test_instance_creation.py with unit tests for task instance creation
- [ ] T-705 [US6] Create integration test for full generation cycle (create pattern → run generator → verify instances)

### Deployment Configuration

- [ ] T-706 [US6] Create k8s/cronjob-recurring-generator.yaml with CronJob (schedule: "0 2 * * *", timezone: UTC)
- [ ] T-707 [US6] Configure CronJob with timeout (30 minutes), backoffLimit (3 retries), restartPolicy (OnFailure)
- [ ] T-708 [US6] Add environment variables in CronJob: DATABASE_URL, DAPR_HTTP_PORT
- [ ] T-709 [US6] Add resource limits in CronJob pod spec (CPU: 500m, Memory: 256Mi)
- [ ] T-710 [US6] Document manual CronJob trigger command in specs/005-phase5-advanced-cloud/recurring-generator-runbook.md

**Checkpoint**: Recurring Task Generator deployed as CronJob ✅

**Dependencies for Next Phase**: Recurring generator publishes events (consumed by Reminder Service)

---

## Phase 9: Frontend UI Extensions (US8)

**Goal**: Update Next.js frontend to support due dates, reminders, and recurring patterns.

**Plan Reference**: Service 6: Frontend section

**Independent Test**:
- Create task with due date and reminder
- Create recurring pattern via UI
- View recurring tasks in task list

**Dependencies**: T-563 to T-587 (Backend API endpoints available)

### UI Components for Due Dates and Reminders

- [ ] T-711 [P] [US8] Update frontend/lib/types.ts Task interface with new fields: due_date, reminder_time, reminder_config, is_recurring
- [ ] T-712 [US8] Update frontend/components/TaskForm.tsx to add due date picker (date input field)
- [ ] T-713 [US8] Add reminder time picker in TaskForm.tsx (time input field, conditional on due_date)
- [ ] T-714 [US8] Add reminder channel selection in TaskForm.tsx (checkboxes: email, in-app, webhook)
- [ ] T-715 [US8] Update frontend/lib/api.ts createTask function to include new fields in request body

### Task List UI Updates

- [ ] T-716 [US8] Update frontend/components/TaskList.tsx to display due date (formatted, e.g., "Jan 10, 2026")
- [ ] T-717 [US8] Add visual indicator for tasks with reminders (bell icon)
- [ ] T-718 [US8] Add visual indicator for recurring tasks (repeat icon, badge)
- [ ] T-719 [US8] Add overdue task highlighting (red text if due_date < today and not completed)

### Recurring Patterns UI

- [ ] T-720 [US8] Create frontend/components/RecurringPatternForm.tsx with form fields: task template (title, description, priority), frequency (dropdown), interval, days_of_week, end_date
- [ ] T-721 [US8] Add frequency-specific fields in RecurringPatternForm.tsx (show days_of_week only if weekly, day_of_month only if monthly)
- [ ] T-722 [US8] Create frontend/app/recurring/page.tsx to list user's recurring patterns
- [ ] T-723 [US8] Add "Create Recurring Task" button in dashboard linking to recurring pattern form
- [ ] T-724 [US8] Add frontend/lib/api.ts functions for recurring patterns (createRecurringPattern, getRecurringPatterns, updateRecurringPattern, deleteRecurringPattern)

### In-App Notifications UI (Optional)

- [ ] T-725 [P] [US8] Create frontend/components/NotificationBell.tsx with notification icon and badge (unread count)
- [ ] T-726 [P] [US8] Add notifications dropdown in Navbar.tsx (show recent reminders)
- [ ] T-727 [P] [US8] Create frontend/lib/notifications.ts with notification polling logic (fetch recent reminders every 30 seconds)

### Form Validation

- [ ] T-728 [US8] Add client-side validation in TaskForm.tsx: due_date must be future date, reminder_time must be before due_date
- [ ] T-729 [US8] Add validation in RecurringPatternForm.tsx: interval > 0, end_date must be future, at least one day selected for weekly

### Testing

- [ ] T-730 [P] [US8] Manual test checklist in specs/005-phase5-advanced-cloud/frontend-test-checklist.md (create task with reminder, create recurring pattern, view notifications)
- [ ] T-731 [P] [US8] Screenshot key UI screens and save to specs/005-phase5-advanced-cloud/screenshots/ (task form, recurring form, task list)

**Checkpoint**: Frontend UI supports Phase V features ✅

**Dependencies for Next Phase**: Frontend ready for end-to-end testing

---

## Phase 10: Helm Chart Updates (US9, US10)

**Goal**: Update Helm chart to include all Phase V services with separate values for local and cloud.

**Plan Reference**: Deployment Topology, Local vs Cloud Differences sections

**Independent Test**:
- `helm template ./helm/todo-app -f values-local.yaml` (verify manifests generated)
- `helm install todo-app ./helm/todo-app -f values-local.yaml` (deploy to Minikube)
- `helm status todo-app` (verify all pods running)

**Dependencies**: All services implemented (T-588 to T-710)

### Chart Structure Updates

- [ ] T-732 [US9] Update helm/todo-app/Chart.yaml version to 2.0.0 (Phase V release)
- [ ] T-733 [US9] Update helm/todo-app/values.yaml with default values for Phase V services
- [ ] T-734 [US9] Add reminder service configuration in values.yaml (replicas: 1, resources, image)
- [ ] T-735 [US9] Add notification service configuration in values.yaml (replicas: 2, resources, image)
- [ ] T-736 [US9] Add audit service configuration in values.yaml (replicas: 1, resources, image)
- [ ] T-737 [US9] Add recurring generator configuration in values.yaml (schedule, resources, image)
- [ ] T-738 [US9] Add Kafka configuration in values.yaml (enabled: true, replicaCount, persistence)
- [ ] T-739 [US9] Add Dapr configuration in values.yaml (pubsub type, component config)

### Service Templates

- [ ] T-740 [US9] Create helm/todo-app/templates/deployment-reminder-service.yaml (templated from k8s/deployment-reminder-service.yaml)
- [ ] T-741 [US9] Create helm/todo-app/templates/service-reminder-service.yaml
- [ ] T-742 [US9] Create helm/todo-app/templates/deployment-notification-service.yaml
- [ ] T-743 [US9] Create helm/todo-app/templates/service-notification-service.yaml
- [ ] T-744 [US9] Create helm/todo-app/templates/deployment-audit-service.yaml
- [ ] T-745 [US9] Create helm/todo-app/templates/service-audit-service.yaml
- [ ] T-746 [US9] Create helm/todo-app/templates/cronjob-recurring-generator.yaml
- [ ] T-747 [US9] Update helm/todo-app/templates/deployment-backend.yaml to add Dapr annotations

### Dapr Component Templates

- [ ] T-748 [US9] Create helm/todo-app/templates/dapr-pubsub-redis.yaml (conditional: if .Values.dapr.pubsub.type == "redis")
- [ ] T-749 [US9] Create helm/todo-app/templates/dapr-pubsub-kafka.yaml (conditional: if .Values.dapr.pubsub.type == "kafka")

### ConfigMaps and Secrets

- [ ] T-750 [US9] Update helm/todo-app/templates/configmap.yaml with Phase V environment variables (DAPR_HTTP_PORT, etc.)
- [ ] T-751 [US9] Update helm/todo-app/templates/secret.yaml template to include SENDGRID_API_KEY placeholder

### Local Values File

- [ ] T-752 [US9] Create helm/todo-app/values-local.yaml with Minikube-optimized values
- [ ] T-753 [US9] Configure local values: kafka.replicaCount: 1, kafka.persistence: false, dapr.pubsub.type: redis
- [ ] T-754 [US9] Set minimal resource requests/limits in local values (128Mi-256Mi RAM)
- [ ] T-755 [US9] Set replica counts in local values: reminder: 1, notification: 1, audit: 1

### Cloud Values File

- [ ] T-756 [US10] Create helm/todo-app/values-production.yaml with cloud-optimized values
- [ ] T-757 [US10] Configure production values: kafka.replicaCount: 3, kafka.persistence: true, dapr.pubsub.type: kafka
- [ ] T-758 [US10] Set production resource requests/limits (512Mi-2Gi RAM)
- [ ] T-759 [US10] Set replica counts for HA: reminder: 2, notification: 3, audit: 2
- [ ] T-760 [US10] Add autoscaling configuration in production values (HPA enabled, minReplicas, maxReplicas)
- [ ] T-761 [US10] Add ingress TLS configuration in production values (secretName, hosts)

### Deployment Scripts

- [ ] T-762 [US9] Create k8s/deploy-local.sh script to deploy to Minikube with Helm (helm install ... -f values-local.yaml)
- [ ] T-763 [US9] Add prerequisite checks in deploy-local.sh (minikube running, Dapr installed, Kafka installed)
- [ ] T-764 [US9] Add post-deployment validation in deploy-local.sh (wait for pods ready, run health checks)
- [ ] T-765 [US10] Create k8s/deploy-production.sh script to deploy to cloud with Helm (helm install ... -f values-production.yaml)
- [ ] T-766 [US10] Add cloud prerequisite checks in deploy-production.sh (kubectl context, managed Kafka configured)

### Validation Scripts

- [ ] T-767 [US9] Update k8s/validation-summary.sh to include Phase V services (reminder, notification, audit, recurring)
- [ ] T-768 [US9] Add Dapr component validation checks (kubectl get components)
- [ ] T-769 [US9] Add Kafka topic validation checks (list topics, verify retention)
- [ ] T-770 [US9] Add event flow validation (publish test event, verify consumed by services)

**Checkpoint**: Helm chart updated, local and cloud deployments ready ✅

**Dependencies for Next Phase**: Helm chart ready for CI/CD integration

---

## Phase 11: CI/CD Pipeline Implementation (US11)

**Goal**: Create GitHub Actions workflows for automated build, test, and deployment.

**Plan Reference**: ADR-005-009, CI/CD Pipeline section

**Independent Test**:
- Push commit to develop branch
- Verify workflow triggers and passes all stages
- Verify dev deployment successful

**Dependencies**: T-732 to T-770 (Helm chart ready), all services implemented

### Workflow Structure

- [ ] T-771 [US11] Create .github/workflows/ci-cd.yaml with workflow skeleton (name, triggers)
- [ ] T-772 [US11] Add workflow triggers in ci-cd.yaml: push to main, develop branches, pull_request to main
- [ ] T-773 [US11] Add workflow environment variables: REGISTRY (ghcr.io), IMAGE_PREFIX (todo-)

### Build Stage

- [ ] T-774 [US11] Add "Build and Lint" job in ci-cd.yaml
- [ ] T-775 [US11] Add backend linting step (pylint, mypy) for backend and all services
- [ ] T-776 [US11] Add frontend linting step (eslint, tsc --noEmit)
- [ ] T-777 [US11] Add Dockerfile linting step (hadolint) for all Dockerfiles

### Test Stage

- [ ] T-778 [US11] Add "Unit Tests" job in ci-cd.yaml (runs in parallel with Build)
- [ ] T-779 [US11] Add backend unit tests step (pytest backend/tests/ with coverage report)
- [ ] T-780 [US11] Add service unit tests steps (pytest services/*/tests/)
- [ ] T-781 [US11] Add coverage requirement check (fail if coverage < 80%)

- [ ] T-782 [P] [US11] Add "Integration Tests" job in ci-cd.yaml (depends on Build)
- [ ] T-783 [P] [US11] Add Docker Compose setup for integration tests (Postgres, Redis, Kafka)
- [ ] T-784 [P] [US11] Add integration test step (pytest backend/tests/integration/)

### Security Scanning

- [ ] T-785 [US11] Add "Security Scan" job in ci-cd.yaml (runs in parallel with Tests)
- [ ] T-786 [US11] Add Trivy image scanning step for all Docker images
- [ ] T-787 [US11] Add dependency scanning step (safety check for Python, npm audit for Node.js)
- [ ] T-788 [US11] Add secret scanning step (detect-secrets)

### Package Stage

- [ ] T-789 [US11] Add "Build and Push Images" job in ci-cd.yaml (depends on Build, Test, Security Scan)
- [ ] T-790 [US11] Add Docker build step for backend image (docker build -t ghcr.io/.../todo-backend:$SHA)
- [ ] T-791 [US11] Add Docker build step for frontend image
- [ ] T-792 [US11] Add Docker build steps for service images (reminder, notification, audit, recurring)
- [ ] T-793 [US11] Add Docker push step to GitHub Container Registry (ghcr.io)
- [ ] T-794 [US11] Add image tagging logic (tag with commit SHA, branch name, and 'latest' for main)

### Deploy Dev Stage

- [ ] T-795 [US11] Add "Deploy to Dev" job in ci-cd.yaml (depends on Package, only for develop branch)
- [ ] T-796 [US11] Add kubectl context setup step (configure access to dev cluster)
- [ ] T-797 [US11] Add Helm upgrade step (helm upgrade --install todo-app ./helm/todo-app -f values-dev.yaml)
- [ ] T-798 [US11] Add deployment wait step (kubectl rollout status)
- [ ] T-799 [US11] Add smoke test step (curl health endpoints)

### Deploy Staging Stage

- [ ] T-800 [US11] Add "Deploy to Staging" job in ci-cd.yaml (depends on Deploy Dev, only for main branch)
- [ ] T-801 [US11] Add Helm upgrade step for staging cluster (-f values-staging.yaml)
- [ ] T-802 [US11] Add deployment wait and health check

### E2E Tests on Staging

- [ ] T-803 [US11] Add "E2E Tests" job in ci-cd.yaml (depends on Deploy Staging)
- [ ] T-804 [US11] Add Playwright/Cypress setup step
- [ ] T-805 [US11] Add E2E test execution step (run against staging environment)
- [ ] T-806 [US11] Add test artifact upload (screenshots, videos on failure)

### Deploy Production Stage

- [ ] T-807 [US11] Add "Deploy to Production" job in ci-cd.yaml (depends on E2E Tests, manual approval required)
- [ ] T-808 [US11] Add manual approval gate using GitHub Environments (environment: production, required reviewers)
- [ ] T-809 [US11] Add Helm upgrade step for production cluster (-f values-production.yaml)
- [ ] T-810 [US11] Add deployment wait and health check
- [ ] T-811 [US11] Add production smoke test step

### Post-Deployment

- [ ] T-812 [US11] Add "Smoke Test Production" job in ci-cd.yaml (depends on Deploy Production)
- [ ] T-813 [US11] Add critical path tests (user registration, task creation, reminder scheduling)
- [ ] T-814 [US11] Add rollback step on smoke test failure (helm rollback todo-app)

### Notifications

- [ ] T-815 [P] [US11] Add "Notify" job in ci-cd.yaml (runs always, depends on all previous jobs)
- [ ] T-816 [P] [US11] Add Slack notification step (success/failure message to #deployments channel)
- [ ] T-817 [P] [US11] Add deployment summary comment to PR (if triggered by pull_request)

### Workflow Testing

- [ ] T-818 [US11] Create .github/workflows/test-workflow.yaml for testing workflow changes (triggers on push to .github/workflows/)
- [ ] T-819 [US11] Test workflow locally using act (https://github.com/nektos/act) and document in specs/005-phase5-advanced-cloud/ci-cd-testing.md
- [ ] T-820 [US11] Document workflow stages and execution time in specs/005-phase5-advanced-cloud/ci-cd-pipeline-doc.md

**Checkpoint**: CI/CD pipeline operational, automated deployments working ✅

**Dependencies for Next Phase**: CI/CD pipeline ready for production use

---

## Phase 12: Testing, Validation, and Documentation (US12)

**Goal**: Comprehensive testing, validation scripts, and complete documentation for Phase V.

**Plan Reference**: Validation Strategy, Success Criteria sections

**Independent Test**:
- Run validation script: `./k8s/validate-phase5.sh`
- Run performance tests: `k6 run tests/performance/task-creation.js`
- Verify all success criteria met

**Dependencies**: All previous phases complete (T-501 to T-820)

### End-to-End Testing

- [ ] T-821 [US12] Create tests/e2e/test_event_flow.py with end-to-end event flow test (task creation → reminder → notification)
- [ ] T-822 [US12] Create tests/e2e/test_recurring_tasks.py with recurring pattern creation and instance generation test
- [ ] T-823 [US12] Create tests/e2e/test_reminders.py with reminder scheduling and firing test
- [ ] T-824 [US12] Add E2E test execution script tests/e2e/run-e2e-tests.sh
- [ ] T-825 [US12] Execute E2E tests against Minikube deployment and record results in specs/005-phase5-advanced-cloud/e2e-test-report.md

### Performance Testing

- [ ] T-826 [P] [US12] Create tests/performance/task-creation.js k6 script (test task creation throughput: target 100 req/sec)
- [ ] T-827 [P] [US12] Create tests/performance/event-processing.js k6 script (test event publishing and consumption lag)
- [ ] T-828 [P] [US12] Create tests/performance/reminder-load.js script (test 10,000 reminders scheduled)
- [ ] T-829 [US12] Execute performance tests and record results in specs/005-phase5-advanced-cloud/performance-test-report.md
- [ ] T-830 [US12] Verify performance meets targets: p95 latency <200ms, event lag <1 second, reminder accuracy within 1 minute

### Chaos Testing (Optional)

- [ ] T-831 [P] [US12] Create tests/chaos/test-kafka-failure.sh script (kill Kafka broker, verify recovery)
- [ ] T-832 [P] [US12] Create tests/chaos/test-service-crash.sh script (kill reminder service pod, verify scheduler state recovery)
- [ ] T-833 [P] [US12] Execute chaos tests and document results in specs/005-phase5-advanced-cloud/chaos-test-report.md

### Validation Scripts

- [ ] T-834 [US12] Create k8s/validate-phase5.sh comprehensive validation script
- [ ] T-835 [US12] Add validation checks in script: all Phase V pods running, Dapr components created, Kafka topics exist, database tables exist
- [ ] T-836 [US12] Add event flow validation: publish test event via Backend API, verify consumed by Audit Service
- [ ] T-837 [US12] Add reminder flow validation: create task with reminder, verify scheduled in APScheduler
- [ ] T-838 [US12] Add recurring flow validation: trigger CronJob manually, verify instances created
- [ ] T-839 [US12] Add health check validation: curl all service health endpoints
- [ ] T-840 [US12] Execute validation script and record output in specs/005-phase5-advanced-cloud/validation-report.md

### Documentation

- [ ] T-841 [P] [US12] Create specs/005-phase5-advanced-cloud/ARCHITECTURE.md with detailed architecture diagrams (services, event flows, deployment topology)
- [ ] T-842 [P] [US12] Create specs/005-phase5-advanced-cloud/DEPLOYMENT-RUNBOOK.md with step-by-step deployment instructions (local and cloud)
- [ ] T-843 [P] [US12] Update specs/005-phase5-advanced-cloud/plan.md with any architecture changes discovered during implementation
- [ ] T-844 [P] [US12] Create specs/005-phase5-advanced-cloud/TROUBLESHOOTING.md with common issues and solutions
- [ ] T-845 [P] [US12] Create specs/005-phase5-advanced-cloud/API-DOCUMENTATION.md with updated API endpoints (recurring patterns, reminders)

### User Documentation

- [ ] T-846 [P] [US12] Create docs/user-guide/reminders.md with user guide for setting reminders
- [ ] T-847 [P] [US12] Create docs/user-guide/recurring-tasks.md with user guide for creating recurring patterns
- [ ] T-848 [P] [US12] Update README.md with Phase V overview and features

### Observability Setup

- [ ] T-849 [US12] Create k8s/monitoring/prometheus-config.yaml with Prometheus configuration (scrape configs for all services)
- [ ] T-850 [US12] Create k8s/monitoring/grafana-dashboards/ directory with Grafana dashboard JSON files
- [ ] T-851 [US12] Create dashboard: Application Overview (request rate, latency, error rate)
- [ ] T-852 [US12] Create dashboard: Event Processing (Kafka lag, event consumption rate, processing errors)
- [ ] T-853 [US12] Create dashboard: Reminders (scheduled vs fired, firing accuracy, failed reminders)
- [ ] T-854 [US12] Create dashboard: Infrastructure (Kafka broker metrics, Dapr sidecar latency, database connections)
- [ ] T-855 [US12] Document dashboard installation in specs/005-phase5-advanced-cloud/observability-setup.md

### Success Criteria Verification

- [ ] T-856 [US12] Create specs/005-phase5-advanced-cloud/SUCCESS-CRITERIA.md checklist
- [ ] T-857 [US12] Verify Functional Criteria (14 items) and check off in SUCCESS-CRITERIA.md
- [ ] T-858 [US12] Verify Non-Functional Criteria (performance, reliability, scalability, security, observability) and check off
- [ ] T-859 [US12] Verify Documentation Criteria (architecture docs, runbooks, API docs, user guides) and check off
- [ ] T-860 [US12] Verify Testing Criteria (unit, integration, E2E, performance tests) and check off

### Final Reports

- [ ] T-861 [US12] Create specs/005-phase5-advanced-cloud/IMPLEMENTATION-SUMMARY.md with statistics (files created, lines of code, services deployed)
- [ ] T-862 [US12] Create specs/005-phase5-advanced-cloud/PHASE-V-COMPLETE.md final summary document (similar to Phase IV PHASE-IV-COMPLETE.md)
- [ ] T-863 [US12] Update speckit.specify with Phase V completion status

**Checkpoint**: Phase V complete, production-ready ✅

---

## Task Dependencies Summary

### Critical Path (must be sequential)

1. **Database Foundation** (T-501 to T-518) → All services depend on schema
2. **Event Schemas** (T-519 to T-540) → All services depend on event models
3. **Infrastructure** (T-541 to T-562) → Services need Kafka and Dapr
4. **Backend API** (T-563 to T-587) → Services consume events from Backend
5. **Services** (T-588 to T-710) → Can run in parallel after Backend API ready
6. **Frontend** (T-711 to T-731) → Depends on Backend API endpoints
7. **Helm Chart** (T-732 to T-770) → Depends on all services ready
8. **CI/CD** (T-771 to T-820) → Depends on Helm chart
9. **Testing & Validation** (T-821 to T-863) → Final phase, depends on all

### Parallel Opportunities

**Phase 1 (Database)**: T-504/505/506, T-507/508/509, T-510/511, T-512/513/514 can run in parallel (different tables)

**Phase 2 (Events)**: Event schema definitions (T-521 to T-528) and SQLModel extensions (T-530 to T-533) can run in parallel

**Phase 3 (Infrastructure)**: Kafka setup (T-541 to T-550) and Dapr setup (T-551 to T-562) can run in parallel

**Phase 5-8 (Services)**: After Backend API complete, all 4 services (Reminder, Notification, Audit, Recurring) can be implemented in parallel

**Phase 12 (Testing)**: E2E tests (T-821 to T-825), performance tests (T-826 to T-830), chaos tests (T-831 to T-833), and documentation (T-841 to T-848) can run in parallel

---

## Task Execution Estimates

**Total Tasks**: 363 tasks (T-501 to T-863)

**Estimated Timeline** (with parallel execution):
- Phase 1 (Database): 2-3 days
- Phase 2 (Events): 2-3 days
- Phase 3 (Infrastructure): 3-4 days
- Phase 4 (Backend API): 3-4 days
- Phase 5-8 (Services): 5-7 days (parallel)
- Phase 9 (Frontend): 3-4 days
- Phase 10 (Helm): 2-3 days
- Phase 11 (CI/CD): 3-4 days
- Phase 12 (Testing): 4-5 days

**Total**: 27-37 days (calendar time with parallel work)

---

## Ready for Implementation

**Prerequisites Verified**:
- ✅ Phase I-IV completed
- ✅ Specification complete (speckit.specify)
- ✅ Planning complete (plan.md)
- ✅ Tasks defined (this file)

**Next Steps**:
1. Approve this task list
2. Begin implementation starting with Phase 1 (Database Migrations)
3. Use `/sp.implement` command or manual task execution
4. Track progress in this file (check off completed tasks)
5. Create PHRs for significant implementation work

---

**End of Tasks**
