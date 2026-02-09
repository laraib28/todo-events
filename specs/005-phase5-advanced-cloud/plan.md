# Phase V Implementation Plan: Advanced Cloud Deployment with Event-Driven Architecture

**Feature**: Event-Driven Architecture with Kafka, Dapr, Reminders, Recurring Tasks, and Cloud Deployment
**Branch**: `005-phase5-advanced-cloud`
**Created**: 2026-01-08
**Status**: Planning
**Input**: Phase V specification from `/speckit.specify`

---

## Executive Summary

This plan defines the architecture and design decisions (HOW) for implementing Phase V: Advanced Cloud Deployment. Building on Phase IV's Kubernetes foundation, Phase V transforms the Todo application into a production-ready, event-driven system with:

- **Event-Driven Architecture**: Asynchronous messaging via Kafka for decoupled, scalable services
- **Task Reminders**: Time-based notifications for task deadlines across multiple channels
- **Recurring Tasks**: Automated generation of repeating tasks based on user-defined schedules
- **Dapr Integration**: Cloud-agnostic messaging abstraction with sidecar pattern
- **Dual Deployment**: Minikube (local development) and Cloud Kubernetes (production)
- **CI/CD Pipeline**: Automated build, test, and deployment workflows

**Key Architectural Principle**: Event-driven, microservices-based architecture with clear service boundaries, leveraging Dapr for cloud portability and Kafka for reliable event streaming.

---

## Table of Contents

1. [Planning Overview](#planning-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Service Architecture](#service-architecture)
4. [Event-Driven Architecture](#event-driven-architecture)
5. [Dapr Integration](#dapr-integration)
6. [Service Boundaries](#service-boundaries)
7. [Deployment Topology](#deployment-topology)
8. [Local vs Cloud Differences](#local-vs-cloud-differences)
9. [Sequence Diagrams](#sequence-diagrams)
10. [Data Architecture](#data-architecture)
11. [Security Architecture](#security-architecture)
12. [Observability Architecture](#observability-architecture)
13. [Validation Strategy](#validation-strategy)
14. [Risk Mitigation](#risk-mitigation)
15. [Success Criteria](#success-criteria)

---

## Planning Overview

### Objectives

1. **Primary Goal**: Transform Todo app into event-driven architecture with reminders and recurring tasks
2. **Secondary Goal**: Achieve production readiness with cloud deployment and CI/CD
3. **Tertiary Goal**: Maintain development agility with local Minikube environment

### Design Principles

- **Event-First**: All state changes generate events; services communicate asynchronously
- **Cloud-Agnostic**: Use Dapr abstraction to avoid vendor lock-in
- **Eventual Consistency**: Accept asynchronous processing delays (seconds, not milliseconds)
- **Idempotency**: All event handlers must be idempotent (safe to replay)
- **Observability**: Comprehensive metrics, logs, and traces for all services
- **Graceful Degradation**: Core features work even if event system is degraded

### Constraints

- ✅ **MUST**: Reuse Phase IV Helm/Kubernetes patterns
- ✅ **MUST**: Support both Minikube (local) and Cloud Kubernetes (production)
- ✅ **MUST**: All events persisted to Kafka (durable messaging)
- ✅ **MUST**: Services deployable independently (loose coupling)
- ✅ **MUST**: Backwards compatible with Phase IV (no breaking API changes)
- ❌ **MUST NOT**: Introduce synchronous dependencies between services
- ❌ **MUST NOT**: Hard-code cloud provider specifics (use Dapr abstraction)

### Dependencies

**Prerequisites**:
- Phase I (CLI) - Completed ✅
- Phase II (Web) - Completed ✅
- Phase III (AI Chat) - Completed ✅
- Phase IV (Kubernetes) - Completed ✅

**New External Dependencies**:
- Kafka cluster (Strimzi Operator for Kubernetes or managed service)
- Dapr runtime (control plane + sidecars)
- Email service provider (SendGrid, AWS SES, or similar)
- Cloud provider account (GCP, AWS, or Azure for production)

---

## Architecture Decisions

### ADR-005-001: Event-Driven Architecture with Kafka

**Decision**: Implement event-driven architecture using Apache Kafka as the message broker.

**Context**:
- Application requires decoupled services (reminders, recurring tasks, analytics, audit)
- Need reliable, durable message delivery
- Must support high event throughput (1000+ events/sec)
- Event replay required for recovery scenarios

**Alternatives Considered**:
1. **RabbitMQ**: Good for traditional messaging but weaker event streaming and replay
2. **AWS SQS/SNS**: Cloud-specific, vendor lock-in concerns
3. **Redis Pub/Sub**: Not durable, no replay capability
4. **NATS**: Good performance but smaller ecosystem than Kafka

**Decision Rationale**:
- Kafka provides durable event log with replay capability
- Industry standard for event streaming architectures
- Strong ecosystem and tooling (Kafka Connect, Schema Registry, etc.)
- Horizontal scalability with partitioning
- Works well with Dapr PubSub component

**Consequences**:
- ✅ Reliable, ordered event delivery
- ✅ Event sourcing and replay capabilities
- ✅ Strong ecosystem and community
- ❌ Higher operational complexity than simpler message queues
- ❌ Resource overhead (memory, disk, network)

**Implementation Strategy**:
- Local (Minikube): Single Kafka broker via Strimzi Operator or Bitnami Helm chart
- Cloud (Production): 3-broker cluster for HA (managed service preferred)
- Topic naming: `{domain}.{entity}.{event}` (e.g., `tasks.task.created`)
- Partitioning: By `user_id` for ordering guarantees per user

---

### ADR-005-002: Dapr for Cloud-Agnostic Messaging

**Decision**: Use Dapr (Distributed Application Runtime) as abstraction layer over Kafka.

**Context**:
- Need cloud portability (avoid vendor lock-in)
- Want to simplify service code (abstract away Kafka clients)
- Require unified observability (tracing across services)
- Desire flexibility to swap message brokers (local vs production)

**Alternatives Considered**:
1. **Direct Kafka Clients**: Full control but vendor lock-in and complex code
2. **Spring Cloud Stream**: Java-centric, not polyglot
3. **CloudEvents SDK**: Specification only, no runtime
4. **Custom Abstraction**: Maintenance burden

**Decision Rationale**:
- Dapr provides polyglot, cloud-agnostic runtime for messaging
- Sidecar pattern keeps service code clean
- Built-in observability (tracing, metrics)
- Easy to swap PubSub components (Kafka → Redis → Azure Service Bus)
- Active CNCF project with strong community

**Consequences**:
- ✅ Cloud portability (swap Kafka for managed services)
- ✅ Simplified service code (HTTP/gRPC APIs instead of Kafka clients)
- ✅ Built-in observability and resiliency patterns
- ❌ Additional runtime complexity (sidecar containers)
- ❌ Network hop overhead (service → sidecar → Kafka)

**Implementation Strategy**:
- Dapr installed via Helm chart in Kubernetes
- Sidecar injection via annotations on Deployments
- PubSub component configurations:
  - Local: `pubsub-redis.yaml` (Redis for simplicity)
  - Production: `pubsub-kafka.yaml` (Kafka for durability)
- Services publish/subscribe via Dapr HTTP API (`/v1.0/publish`, `/v1.0/subscribe`)

---

### ADR-005-003: Microservices Architecture with Clear Boundaries

**Decision**: Decompose application into 6 independently deployable services.

**Context**:
- Event-driven architecture requires multiple event consumers
- Reminders and recurring tasks have distinct lifecycles
- Need independent scaling (e.g., scale notification service separately)
- Want team autonomy (different teams can own different services)

**Service Boundaries**:
1. **Backend API** (existing, extended)
2. **Reminder Service** (new)
3. **Recurring Task Generator** (new)
4. **Notification Service** (new)
5. **Audit Service** (new)
6. **Frontend** (existing, unchanged)

**Decision Rationale**:
- Each service has single responsibility
- Services can scale independently based on load
- Team autonomy and parallel development
- Failure isolation (reminder failure doesn't break task CRUD)

**Consequences**:
- ✅ Independent deployment and scaling
- ✅ Failure isolation and resilience
- ✅ Clear ownership and responsibility
- ❌ Increased operational complexity (6 services vs 2)
- ❌ Distributed tracing required for debugging

**Implementation Strategy**:
- Each service is a separate Deployment in Kubernetes
- Services communicate only via events (no direct HTTP calls between services)
- Shared database (PostgreSQL) for Phase V, migrate to per-service DBs in future
- Each service has its own health checks, metrics, and logging

---

### ADR-005-004: Reminder Service Architecture

**Decision**: Implement reminder service as continuously running scheduler with database-backed state.

**Context**:
- Reminders must fire within 1 minute of scheduled time
- System must handle 100,000+ active reminders
- Reminders must survive pod restarts (persistent state)
- Must support timezone-aware scheduling

**Alternatives Considered**:
1. **Kubernetes CronJob**: Not suitable for dynamic, per-task schedules
2. **Celery Beat**: Python-specific, requires Redis backend
3. **APScheduler with PostgreSQL JobStore**: Lightweight, Python-friendly
4. **Temporal/Cadence**: Overkill for simple scheduling

**Decision Rationale**:
- APScheduler with PostgreSQL JobStore provides:
  - Persistent job storage (survives restarts)
  - Timezone-aware scheduling
  - Python-native (matches backend stack)
  - Lightweight (no additional infrastructure)

**Architecture**:
```
Reminder Service:
├── Event Listener (Dapr subscriber)
│   └── Listens to: tasks.task.created, tasks.task.updated
│   └── Schedules reminders in APScheduler
├── APScheduler (with PostgreSQL JobStore)
│   └── Triggers reminder jobs at scheduled times
├── Reminder Executor
│   └── Publishes reminders.reminder.fired event
└── Database
    └── reminders table (tracks reminder state)
    └── apscheduler_jobs table (scheduler state)
```

**Consequences**:
- ✅ Accurate scheduling (within 1 minute)
- ✅ Survives pod restarts (state in PostgreSQL)
- ✅ Timezone-aware
- ❌ Single point of failure (one scheduler instance)
- ❌ Need leader election for HA (future enhancement)

**Implementation Strategy**:
- Deploy as Kubernetes Deployment (1 replica initially)
- Use APScheduler with PostgreSQL JobStore
- Subscribe to `tasks.task.created` and `tasks.task.updated` events
- Publish `reminders.reminder.fired` events
- Store reminder state in PostgreSQL `reminders` table

---

### ADR-005-005: Recurring Task Generator as Scheduled Job

**Decision**: Implement recurring task generator as Kubernetes CronJob running daily.

**Context**:
- Recurring tasks need generation once per day (not real-time)
- Generation is batch process (query patterns, create instances)
- Failure can be retried next day (not time-critical)

**Alternatives Considered**:
1. **Continuous Service**: Resource waste for once-daily job
2. **Event-Driven**: No clear trigger event (time-based, not event-based)
3. **Lambda/Cloud Function**: Adds cloud dependency

**Decision Rationale**:
- CronJob is native Kubernetes resource for scheduled tasks
- Resource-efficient (pod only runs when needed)
- Failure retries built-in (backoffLimit)
- Simple and predictable

**Architecture**:
```
Recurring Task Generator (CronJob):
├── Scheduled: Daily at 2:00 AM UTC
├── Query: Find recurrence patterns needing new instances
├── Generate: Create task instances for next 30 days
├── Publish: tasks.task.created event for each instance
└── Update: Last generation timestamp on patterns
```

**Consequences**:
- ✅ Resource-efficient (runs only when needed)
- ✅ Simple and predictable
- ✅ Built-in retry logic
- ❌ Not real-time (24-hour delay for new patterns)
- ❌ Long-running job (thousands of patterns could take minutes)

**Implementation Strategy**:
- Deploy as Kubernetes CronJob (schedule: `0 2 * * *`)
- Python script queries `recurrence_patterns` table
- Generates task instances for next 30 days
- Publishes `tasks.task.created` event for each instance
- Job timeout: 30 minutes, backoffLimit: 3

---

### ADR-005-006: Notification Service for Multi-Channel Delivery

**Decision**: Create dedicated notification service handling all outbound notifications.

**Context**:
- Notifications sent via multiple channels (email, in-app, webhook)
- Different channels have different delivery mechanisms
- Notification logic should not pollute other services
- Need retry and failure handling for delivery

**Architecture**:
```
Notification Service:
├── Event Listener (Dapr subscriber)
│   └── Listens to: reminders.reminder.fired, tasks.task.assigned, etc.
├── Channel Handlers
│   ├── Email Handler (SendGrid/AWS SES)
│   ├── In-App Handler (WebSocket broadcast)
│   └── Webhook Handler (HTTP POST to user URLs)
├── Template Engine
│   └── Jinja2 templates for email/messages
├── Retry Logic
│   └── Exponential backoff for failed deliveries
└── Notification History
    └── Store in PostgreSQL for audit
```

**Consequences**:
- ✅ Centralized notification logic
- ✅ Easy to add new channels
- ✅ Failure isolation (notification failure doesn't affect reminders)
- ❌ Additional service to operate
- ❌ Potential bottleneck if high notification volume

**Implementation Strategy**:
- Deploy as Kubernetes Deployment (2 replicas for HA)
- Subscribe to `reminders.reminder.fired` and other notification events
- Use SendGrid API for email (configurable via env vars)
- Use WebSocket for in-app notifications (optional, future)
- Store notification history in PostgreSQL

---

### ADR-005-007: Audit Service for Event Logging

**Decision**: Create audit service to persist all events for compliance and debugging.

**Context**:
- Need complete audit trail of all task operations
- Events useful for debugging and analytics
- Separate concern from core business logic

**Architecture**:
```
Audit Service:
├── Event Listener (Dapr subscriber)
│   └── Listens to: tasks.*, reminders.*, recurring.*
├── Event Persister
│   └── Writes all events to events table
└── Query API (optional)
    └── REST API for querying audit logs
```

**Consequences**:
- ✅ Complete audit trail
- ✅ Useful for debugging and analytics
- ✅ Simple implementation (just persist events)
- ❌ High write volume (every event)
- ❌ Database growth (need retention policy)

**Implementation Strategy**:
- Deploy as Kubernetes Deployment (1 replica sufficient)
- Subscribe to all event topics (`tasks.*`, `reminders.*`, `recurring.*`)
- Persist events to PostgreSQL `events` table
- Optional: Expose query API for fetching event history
- Retention policy: 90 days (configurable)

---

### ADR-005-008: Database Strategy (Shared Database for Phase V)

**Decision**: Use shared PostgreSQL database for all services in Phase V.

**Context**:
- Phase IV already uses Neon PostgreSQL
- Microservices best practice is per-service databases
- Migration to per-service DBs is significant effort

**Decision Rationale**:
- Pragmatic approach: shared DB for Phase V, migrate later
- Reduces operational complexity (one database to manage)
- Services still communicate via events (logical decoupling)
- Database can be partitioned in future (Phase VI)

**Consequences**:
- ✅ Simpler operations (one database)
- ✅ Faster implementation (no data migration)
- ✅ ACID transactions across tables (easier consistency)
- ❌ Coupling via shared schema
- ❌ Scaling bottleneck (all services hit same DB)
- ❌ Future migration pain (splitting DB later)

**Mitigation**:
- Services access only their own tables (logical boundaries)
- Use database views/schemas for logical separation
- Plan for migration to per-service DBs in Phase VI

**Implementation Strategy**:
- Extend existing Neon PostgreSQL database
- Add new tables: `recurrence_patterns`, `reminders`, `events`
- Each service has its own database user (future: separate schemas)
- Connection pooling to handle increased load

---

### ADR-005-009: CI/CD Pipeline with GitHub Actions

**Decision**: Implement CI/CD pipeline using GitHub Actions.

**Context**:
- Need automated build, test, and deployment
- GitHub already hosts source code (assumption)
- Want simple, integrated solution

**Alternatives Considered**:
1. **GitLab CI**: Requires GitLab (not GitHub)
2. **Jenkins**: Heavy, requires separate infrastructure
3. **CircleCI**: Third-party service, cost
4. **ArgoCD/FluxCD**: GitOps, more complex setup

**Decision Rationale**:
- GitHub Actions native to GitHub
- Free for public repos, generous free tier for private
- Simple YAML configuration
- Large ecosystem of pre-built actions

**Pipeline Stages**:
```
1. Source → Trigger on push to main/develop
2. Build → Lint, compile, security scan (Trivy)
3. Test → Unit tests, integration tests
4. Package → Build Docker images, push to registry
5. Deploy Dev → Automatic deployment to Minikube (local dev)
6. Deploy Staging → Automatic deployment to staging cluster
7. Test Staging → End-to-end tests on staging
8. Deploy Production → Manual approval + deployment
9. Smoke Test → Validate production deployment
10. Notify → Slack/email notification
```

**Consequences**:
- ✅ Integrated with GitHub
- ✅ Free (within limits)
- ✅ Simple configuration
- ❌ Vendor lock-in to GitHub
- ❌ Limited customization vs self-hosted Jenkins

**Implementation Strategy**:
- Create `.github/workflows/ci-cd.yaml`
- Separate workflows for backend, frontend, services
- Use GitHub Container Registry (ghcr.io) for Docker images
- Secrets stored in GitHub Secrets
- Manual approval step for production deployment

---

### ADR-005-010: Local (Minikube) vs Cloud Deployment Differences

**Decision**: Maintain separate configurations for local and cloud environments.

**Strategy**:
- Use Helm values files for environment-specific configuration
- Local: `values-local.yaml` (optimized for Minikube)
- Cloud: `values-production.yaml` (optimized for GKE/EKS/AKS)

**Key Differences**:

| Component | Local (Minikube) | Cloud (Production) |
|-----------|------------------|-------------------|
| **Kafka** | Single broker (Bitnami Helm chart) | 3-broker cluster (Confluent Cloud or Strimzi) |
| **Dapr PubSub** | Redis (simpler, less resources) | Kafka (durable, scalable) |
| **PostgreSQL** | Neon serverless (unchanged) | Managed PostgreSQL with read replicas |
| **Ingress** | NGINX Ingress (Minikube addon) | Cloud Load Balancer (ALB/GLB) |
| **TLS** | Self-signed or none | Let's Encrypt or cloud-managed certs |
| **Replicas** | 1 per service (resource constrained) | 2-3 per service (HA) |
| **Autoscaling** | Disabled | HPA enabled (CPU/memory targets) |
| **Monitoring** | Optional (metrics-server) | Prometheus + Grafana stack |
| **Logging** | kubectl logs | Centralized (Loki/ELK or cloud logging) |
| **Secrets** | Kubernetes Secrets | External Secrets Operator + cloud secret manager |
| **Resource Limits** | Minimal (256Mi-512Mi RAM) | Production (512Mi-2Gi RAM) |

**Implementation Strategy**:
- Base Helm chart with templated values
- Override with `helm install -f values-local.yaml` or `-f values-production.yaml`
- Document differences in deployment runbook

---

## Service Architecture

### Service Topology Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Kubernetes Cluster                          │
│                     (Minikube or Cloud Provider)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Namespace: todo-app                                         │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │  Frontend   │  │ Backend API │  │  Reminder   │          │  │
│  │  │  (Next.js)  │  │  (FastAPI)  │  │   Service   │          │  │
│  │  │             │  │             │  │             │          │  │
│  │  │  Port: 3000 │  │  Port: 8000 │  │  Port: 8001 │          │  │
│  │  │  Replicas:2 │  │  Replicas:2 │  │  Replicas:1 │          │  │
│  │  └─────────────┘  └──────┬──────┘  └──────┬──────┘          │  │
│  │                           │                 │                 │  │
│  │                           │ [Dapr Sidecar] │ [Dapr Sidecar]  │  │
│  │                           │                 │                 │  │
│  │  ┌─────────────┐  ┌──────┴──────┐  ┌──────┴──────┐          │  │
│  │  │Notification │  │  Recurring  │  │   Audit     │          │  │
│  │  │   Service   │  │   Task Gen  │  │   Service   │          │  │
│  │  │             │  │  (CronJob)  │  │             │          │  │
│  │  │  Port: 8002 │  │  Schedule:  │  │  Port: 8003 │          │  │
│  │  │  Replicas:2 │  │  Daily 2AM  │  │  Replicas:1 │          │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │  │
│  │         │                 │                 │                 │  │
│  │         │ [Dapr Sidecar] │                 │ [Dapr Sidecar]  │  │
│  │         │                 │                 │                 │  │
│  └─────────┼─────────────────┼─────────────────┼─────────────────┘  │
│            │                 │                 │                    │
│  ┌─────────┴─────────────────┴─────────────────┴─────────────────┐ │
│  │                      Dapr Control Plane                        │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │ │
│  │  │   Sentry   │  │ Placement  │  │  Operator  │               │ │
│  │  │   (mTLS)   │  │  (Actors)  │  │ (Injector) │               │ │
│  │  └────────────┘  └────────────┘  └────────────┘               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Kafka Cluster (Event Bus)                   │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │ │
│  │  │  Broker 0  │  │  Broker 1  │  │  Broker 2  │               │ │
│  │  │ (Leader for│  │ (Leader for│  │ (Leader for│               │ │
│  │  │  partition)│  │  partition)│  │  partition)│               │ │
│  │  └────────────┘  └────────────┘  └────────────┘               │ │
│  │                                                                 │ │
│  │  Topics:                                                        │ │
│  │   - tasks.task.created                                         │ │
│  │   - tasks.task.updated                                         │ │
│  │   - tasks.task.completed                                       │ │
│  │   - tasks.task.deleted                                         │ │
│  │   - reminders.reminder.scheduled                               │ │
│  │   - reminders.reminder.fired                                   │ │
│  │   - recurring.instance.generated                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                PostgreSQL Database (Shared)                     │ │
│  │  Tables:                                                        │ │
│  │   - users (Phase II)                                           │ │
│  │   - tasks (Phase II, extended)                                 │ │
│  │   - recurrence_patterns (Phase V)                              │ │
│  │   - reminders (Phase V)                                        │ │
│  │   - events (Phase V)                                           │ │
│  │   - apscheduler_jobs (Phase V, APScheduler state)              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    NGINX Ingress Controller                     │ │
│  │  Routes:                                                        │ │
│  │   - todo.local → Frontend Service (port 3000)                  │ │
│  │   - api.todo.local → Backend API Service (port 8000)           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
         ▲
         │
         │ HTTPS (production) / HTTP (local)
         │
    ┌────┴─────┐
    │  Users   │
    │ (Browser)│
    └──────────┘
```

---

## Event-Driven Architecture

### Kafka Topic Design

All topics follow the naming convention: `{domain}.{entity}.{event}`

| Topic Name | Partitions | Retention | Description |
|------------|-----------|-----------|-------------|
| `tasks.task.created` | 3 | 7 days | Published when a task is created via API or chat |
| `tasks.task.updated` | 3 | 7 days | Published when a task is updated (title, description, priority) |
| `tasks.task.completed` | 3 | 7 days | Published when a task is marked complete |
| `tasks.task.deleted` | 3 | 7 days | Published when a task is deleted |
| `reminders.reminder.scheduled` | 1 | 7 days | Published when a reminder is scheduled for a task |
| `reminders.reminder.fired` | 1 | 7 days | Published when a reminder fires at scheduled time |
| `reminders.reminder.cancelled` | 1 | 7 days | Published when a reminder is cancelled |
| `recurring.instance.generated` | 3 | 7 days | Published when a recurring task instance is generated |

**Partition Strategy**:
- Tasks topics partitioned by `user_id` (ensures ordering per user)
- Reminders topics use single partition (simpler, lower volume)
- Partition count based on expected throughput (scalable to 6 partitions if needed)

**Retention Policy**:
- 7 days retention for all topics (sufficient for replay scenarios)
- Older events archived to PostgreSQL `events` table (Audit Service)

### Event Schema Design

All events follow CloudEvents specification (https://cloudevents.io/)

**Base Event Schema**:
```json
{
  "specversion": "1.0",
  "type": "com.todoapp.tasks.task.created",
  "source": "backend-api",
  "id": "uuid-v4",
  "time": "2026-01-08T12:34:56Z",
  "datacontenttype": "application/json",
  "data": { ... }
}
```

**Event Payloads**:

#### tasks.task.created
```json
{
  "specversion": "1.0",
  "type": "com.todoapp.tasks.task.created",
  "source": "backend-api",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "time": "2026-01-08T12:34:56Z",
  "subject": "task/123",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "123",
    "user_id": "456",
    "title": "Buy milk",
    "description": "Whole milk, 2 liters",
    "priority": "high",
    "is_completed": false,
    "due_date": "2026-01-10T18:00:00Z",
    "reminder_time": "2026-01-10T17:00:00Z",
    "is_recurring": false,
    "recurrence_pattern_id": null,
    "created_at": "2026-01-08T12:34:56Z"
  }
}
```

#### tasks.task.updated
```json
{
  "specversion": "1.0",
  "type": "com.todoapp.tasks.task.updated",
  "source": "backend-api",
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "time": "2026-01-08T14:00:00Z",
  "subject": "task/123",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "123",
    "user_id": "456",
    "changes": {
      "title": {"old": "Buy milk", "new": "Buy almond milk"},
      "priority": {"old": "high", "new": "medium"}
    },
    "updated_at": "2026-01-08T14:00:00Z"
  }
}
```

#### reminders.reminder.fired
```json
{
  "specversion": "1.0",
  "type": "com.todoapp.reminders.reminder.fired",
  "source": "reminder-service",
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "time": "2026-01-10T17:00:00Z",
  "subject": "reminder/789",
  "datacontenttype": "application/json",
  "data": {
    "reminder_id": "789",
    "task_id": "123",
    "user_id": "456",
    "task_title": "Buy milk",
    "due_date": "2026-01-10T18:00:00Z",
    "notification_channels": ["email", "in_app"],
    "scheduled_time": "2026-01-10T17:00:00Z",
    "fired_at": "2026-01-10T17:00:12Z"
  }
}
```

### Event Flow Patterns

#### Pattern 1: Task Creation with Reminder
```
1. User creates task via API (POST /api/tasks)
2. Backend API:
   - Saves task to database
   - Publishes tasks.task.created event to Kafka (via Dapr)
3. Reminder Service (subscriber):
   - Receives tasks.task.created event
   - If task has reminder_time:
     - Schedules reminder in APScheduler
     - Saves reminder to database
     - Publishes reminders.reminder.scheduled event
4. Audit Service (subscriber):
   - Receives tasks.task.created event
   - Persists event to events table
```

#### Pattern 2: Reminder Firing and Notification
```
1. APScheduler triggers reminder job at scheduled time
2. Reminder Service:
   - Publishes reminders.reminder.fired event to Kafka (via Dapr)
   - Updates reminder status to 'fired' in database
3. Notification Service (subscriber):
   - Receives reminders.reminder.fired event
   - Fetches user preferences (email, webhook URL)
   - Sends notification via configured channels:
     - Email: Renders template, calls SendGrid API
     - In-App: Publishes to WebSocket (future)
     - Webhook: HTTP POST to user's webhook URL
   - Stores notification history in database
4. Audit Service (subscriber):
   - Receives reminders.reminder.fired event
   - Persists event to events table
```

#### Pattern 3: Recurring Task Generation
```
1. Kubernetes CronJob triggers at 2:00 AM UTC daily
2. Recurring Task Generator:
   - Queries recurrence_patterns table for patterns needing instances
   - For each pattern:
     - Generates task instances for next 30 days (if not already generated)
     - For each instance:
       - Saves task to database
       - Publishes recurring.instance.generated event to Kafka
3. Reminder Service (subscriber):
   - Receives recurring.instance.generated event
   - If instance has reminder_time:
     - Schedules reminder in APScheduler
     - Publishes reminders.reminder.scheduled event
4. Audit Service (subscriber):
   - Receives recurring.instance.generated event
   - Persists event to events table
```

---

## Dapr Integration

### Dapr Components

#### Component 1: PubSub (Kafka for Production)

**File**: `k8s/dapr-components/pubsub-kafka.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: todo-app
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka-broker-0.kafka-broker-svc.todo-app.svc.cluster.local:9092"
  - name: authType
    value: "none"  # Production: SASL/SSL
  - name: consumerGroup
    value: "{appId}"
  - name: clientID
    value: "{appId}"
scopes:
- backend-api
- reminder-service
- notification-service
- audit-service
```

#### Component 2: PubSub (Redis for Local)

**File**: `k8s/dapr-components/pubsub-redis.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: todo-app
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: "redis-master.todo-app.svc.cluster.local:6379"
  - name: redisPassword
    secretKeyRef:
      name: redis
      key: redis-password
scopes:
- backend-api
- reminder-service
- notification-service
- audit-service
```

### Dapr Sidecar Injection

Services opt-in to Dapr via Deployment annotations:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: todo-app
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "backend-api"
        dapr.io/app-port: "8000"
        dapr.io/log-level: "info"
        dapr.io/enable-metrics: "true"
        dapr.io/metrics-port: "9090"
    spec:
      containers:
      - name: backend-api
        image: todo-backend:latest
        ports:
        - containerPort: 8000
```

**Annotations Explained**:
- `dapr.io/enabled`: Enable Dapr sidecar injection
- `dapr.io/app-id`: Unique app identifier (used for service discovery)
- `dapr.io/app-port`: Port where service listens (Dapr routes traffic here)
- `dapr.io/log-level`: Logging verbosity (debug, info, warn, error)
- `dapr.io/enable-metrics`: Enable Prometheus metrics endpoint
- `dapr.io/metrics-port`: Port for metrics scraping

### Dapr API Usage

#### Publishing Events

**Backend API (Python/FastAPI)**:
```python
import httpx

async def publish_event(topic: str, event_data: dict):
    """Publish event via Dapr PubSub"""
    dapr_url = "http://localhost:3500/v1.0/publish/pubsub/{topic}"

    event = {
        "specversion": "1.0",
        "type": f"com.todoapp.{topic}",
        "source": "backend-api",
        "id": str(uuid.uuid4()),
        "time": datetime.utcnow().isoformat() + "Z",
        "datacontenttype": "application/json",
        "data": event_data
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            dapr_url.format(topic=topic),
            json=event,
            headers={"Content-Type": "application/cloudevents+json"}
        )
        response.raise_for_status()
```

**Usage in Task Creation**:
```python
@router.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    # Save task to database
    db_task = Task(**task.dict(), user_id=current_user.id)
    db.add(db_task)
    db.commit()

    # Publish event via Dapr
    await publish_event("tasks.task.created", {
        "task_id": str(db_task.id),
        "user_id": str(current_user.id),
        "title": db_task.title,
        "description": db_task.description,
        "priority": db_task.priority,
        "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
        "reminder_time": db_task.reminder_time.isoformat() if db_task.reminder_time else None,
        "created_at": db_task.created_at.isoformat()
    })

    return db_task
```

#### Subscribing to Events

**Reminder Service (Python)**:
```python
from fastapi import FastAPI, Request

app = FastAPI()

# Dapr subscription endpoint
@app.get("/dapr/subscribe")
async def subscribe():
    """Return subscription configuration for Dapr"""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "tasks.task.created",
            "route": "/events/task-created"
        },
        {
            "pubsubname": "pubsub",
            "topic": "tasks.task.updated",
            "route": "/events/task-updated"
        }
    ]

# Event handler
@app.post("/events/task-created")
async def handle_task_created(request: Request):
    """Handle task created event"""
    event = await request.json()
    task_data = event["data"]

    # Schedule reminder if present
    if task_data.get("reminder_time"):
        reminder_time = datetime.fromisoformat(task_data["reminder_time"])
        schedule_reminder(
            task_id=task_data["task_id"],
            user_id=task_data["user_id"],
            reminder_time=reminder_time
        )

    return {"status": "SUCCESS"}
```

---

## Service Boundaries

### Service 1: Backend API (Existing, Extended)

**Responsibility**: Core task CRUD operations, user authentication, event publishing

**Owned Tables**:
- `users`
- `tasks`

**Published Events**:
- `tasks.task.created`
- `tasks.task.updated`
- `tasks.task.completed`
- `tasks.task.deleted`

**Subscribed Events**: None (does not consume events)

**API Endpoints** (extended from Phase III):
```
# Authentication (existing)
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout

# Tasks (existing)
GET    /api/tasks
POST   /api/tasks
GET    /api/tasks/{id}
PUT    /api/tasks/{id}
PATCH  /api/tasks/{id}/toggle
DELETE /api/tasks/{id}

# Recurring Patterns (new)
POST   /api/tasks/recurring
GET    /api/tasks/recurring
GET    /api/tasks/recurring/{id}
PUT    /api/tasks/recurring/{id}
DELETE /api/tasks/recurring/{id}

# Reminders (new)
GET    /api/tasks/{id}/reminders
POST   /api/tasks/{id}/reminders
DELETE /api/reminders/{id}
```

**Technology Stack**:
- Python 3.11
- FastAPI
- SQLModel (ORM)
- httpx (for Dapr HTTP calls)

**Resource Requirements**:
- CPU: 200m request, 1000m limit
- Memory: 256Mi request, 512Mi limit
- Replicas: 2 (HA)

**Health Checks**:
- Liveness: `GET /health`
- Readiness: `GET /ready` (checks DB connection)

---

### Service 2: Reminder Service (New)

**Responsibility**: Schedule and fire reminders for tasks with due dates

**Owned Tables**:
- `reminders`
- `apscheduler_jobs` (APScheduler state)

**Published Events**:
- `reminders.reminder.scheduled`
- `reminders.reminder.fired`
- `reminders.reminder.cancelled`

**Subscribed Events**:
- `tasks.task.created` → Schedule reminder if present
- `tasks.task.updated` → Update or cancel reminder
- `tasks.task.deleted` → Cancel reminder

**Architecture**:
```
Reminder Service
├── FastAPI (HTTP server for Dapr callbacks)
├── APScheduler (with PostgreSQL JobStore)
├── Event Handlers (Dapr subscribers)
└── Reminder Executor (publishes reminder.fired events)
```

**Technology Stack**:
- Python 3.11
- FastAPI (for Dapr event handlers)
- APScheduler (with PostgreSQL JobStore)
- httpx (for Dapr HTTP calls)

**Resource Requirements**:
- CPU: 100m request, 500m limit
- Memory: 128Mi request, 256Mi limit
- Replicas: 1 (single scheduler instance)

**Health Checks**:
- Liveness: `GET /health`
- Readiness: `GET /ready` (checks DB connection and APScheduler status)

**Configuration**:
- APScheduler job store: PostgreSQL
- Timezone: UTC (user timezones handled in job data)
- Misfire grace time: 60 seconds
- Max instances per job: 1

---

### Service 3: Recurring Task Generator (New)

**Responsibility**: Generate task instances for recurring patterns daily

**Owned Tables**:
- `recurrence_patterns`

**Published Events**:
- `recurring.instance.generated` (for each generated task instance)

**Subscribed Events**: None (time-triggered, not event-triggered)

**Architecture**:
```
Recurring Task Generator (CronJob)
├── Query recurrence_patterns (needs new instances)
├── Calculate next 30 days of instances
├── Create task records in database
├── Publish recurring.instance.generated event per instance
└── Update pattern last_generated_at timestamp
```

**Technology Stack**:
- Python 3.11
- SQLAlchemy (direct DB access)
- httpx (for Dapr HTTP calls)
- python-dateutil (for recurrence calculations)

**Resource Requirements** (CronJob pod):
- CPU: 100m request, 500m limit
- Memory: 128Mi request, 256Mi limit
- Timeout: 30 minutes
- Backoff limit: 3 retries

**Schedule**: `0 2 * * *` (daily at 2:00 AM UTC)

**Configuration**:
- Lookahead window: 30 days
- Batch size: 100 patterns per query
- Max instances per pattern per run: 100

---

### Service 4: Notification Service (New)

**Responsibility**: Send notifications via multiple channels (email, in-app, webhook)

**Owned Tables**:
- `notifications` (notification history)

**Published Events**: None (terminal service)

**Subscribed Events**:
- `reminders.reminder.fired` → Send reminder notification

**Architecture**:
```
Notification Service
├── FastAPI (HTTP server for Dapr callbacks)
├── Event Handlers (Dapr subscribers)
├── Channel Handlers
│   ├── EmailHandler (SendGrid API)
│   ├── InAppHandler (WebSocket broadcast, future)
│   └── WebhookHandler (HTTP POST)
├── Template Engine (Jinja2)
└── Retry Logic (exponential backoff)
```

**Technology Stack**:
- Python 3.11
- FastAPI (for Dapr event handlers)
- httpx (for SendGrid API and webhooks)
- Jinja2 (for email templates)
- tenacity (for retry logic)

**Resource Requirements**:
- CPU: 100m request, 500m limit
- Memory: 128Mi request, 256Mi limit
- Replicas: 2 (HA)

**Health Checks**:
- Liveness: `GET /health`
- Readiness: `GET /ready` (checks external API connectivity)

**Configuration**:
- Email provider: SendGrid (configurable)
- SendGrid API key: from Kubernetes Secret
- Email templates: stored in `templates/email/`
- Retry policy: 3 attempts, exponential backoff (1s, 2s, 4s)

**Email Templates**:
- `reminder.html`: Reminder notification email
- `task_assigned.html`: Task assignment notification (future)

---

### Service 5: Audit Service (New)

**Responsibility**: Persist all events for compliance, debugging, and analytics

**Owned Tables**:
- `events` (event log)

**Published Events**: None (terminal service)

**Subscribed Events**:
- `tasks.*` (all task events)
- `reminders.*` (all reminder events)
- `recurring.*` (all recurring task events)

**Architecture**:
```
Audit Service
├── FastAPI (HTTP server for Dapr callbacks)
├── Event Handlers (Dapr subscribers)
├── Event Persister (writes to events table)
└── Query API (optional, for fetching audit logs)
```

**Technology Stack**:
- Python 3.11
- FastAPI (for Dapr event handlers)
- SQLAlchemy (for database access)

**Resource Requirements**:
- CPU: 50m request, 200m limit
- Memory: 64Mi request, 128Mi limit
- Replicas: 1 (single writer sufficient)

**Health Checks**:
- Liveness: `GET /health`
- Readiness: `GET /ready` (checks DB connection)

**Configuration**:
- Retention policy: 90 days (events older than 90 days deleted weekly)
- Batch writes: Buffer 100 events before bulk insert (performance optimization)

**Optional Query API**:
```
GET /api/audit/events?user_id={id}&start_date={date}&end_date={date}
GET /api/audit/events/{event_id}
```

---

### Service 6: Frontend (Existing, Minor Extensions)

**Responsibility**: Web UI for users (task management, AI chat)

**Changes from Phase IV**:
- Add UI for setting due dates and reminders
- Add UI for creating recurring patterns
- Display reminder notifications (in-app)

**Technology Stack**: Next.js 16+, React 19+, TypeScript, Tailwind CSS (unchanged)

**Resource Requirements**: (unchanged from Phase IV)

---

## Deployment Topology

### Kubernetes Resources

#### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: todo-app
  labels:
    name: todo-app
```

#### Deployments

1. **Frontend** (unchanged from Phase IV)
   - Replicas: 2
   - Image: `todo-frontend:latest`
   - Port: 3000

2. **Backend API** (updated with Dapr sidecar)
   - Replicas: 2
   - Image: `todo-backend:latest`
   - Port: 8000
   - Dapr annotations: ✅

3. **Reminder Service** (new)
   - Replicas: 1
   - Image: `todo-reminder-service:latest`
   - Port: 8001
   - Dapr annotations: ✅

4. **Notification Service** (new)
   - Replicas: 2
   - Image: `todo-notification-service:latest`
   - Port: 8002
   - Dapr annotations: ✅

5. **Audit Service** (new)
   - Replicas: 1
   - Image: `todo-audit-service:latest`
   - Port: 8003
   - Dapr annotations: ✅

#### CronJob

6. **Recurring Task Generator** (new)
   - Schedule: `0 2 * * *` (daily 2 AM UTC)
   - Image: `todo-recurring-generator:latest`
   - No Dapr sidecar (publishes directly via HTTP to Dapr API)

#### Services

1. **Frontend Service** (ClusterIP) - unchanged
2. **Backend API Service** (ClusterIP) - unchanged
3. **Reminder Service** (ClusterIP) - new, internal only
4. **Notification Service** (ClusterIP) - new, internal only
5. **Audit Service** (ClusterIP) - new, internal only

#### Kafka Deployment

**Local (Minikube)**:
```yaml
# Using Bitnami Kafka Helm chart
helm install kafka bitnami/kafka \
  --namespace todo-app \
  --set replicaCount=1 \
  --set persistence.enabled=false \
  --set deleteTopicEnable=true
```

**Production (Cloud)**:
- Option 1: Strimzi Operator (self-managed in K8s)
- Option 2: Confluent Cloud (managed Kafka)
- Option 3: AWS MSK / Azure Event Hubs / GCP Pub/Sub (cloud-native alternatives)

#### Dapr Deployment

```bash
# Install Dapr control plane via Helm
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
helm install dapr dapr/dapr --namespace dapr-system --create-namespace

# Apply Dapr components (PubSub)
kubectl apply -f k8s/dapr-components/pubsub-kafka.yaml  # Production
# OR
kubectl apply -f k8s/dapr-components/pubsub-redis.yaml  # Local
```

---

## Local vs Cloud Differences

### Minikube (Local Development)

**Purpose**: Fast iteration, testing, debugging

**Infrastructure**:
- Single-node Kubernetes cluster
- Kafka: Single broker (Bitnami Helm chart, no persistence)
- Dapr PubSub: Redis (simpler than Kafka for local)
- PostgreSQL: Neon serverless (shared with cloud)
- Ingress: Minikube NGINX addon
- TLS: None or self-signed

**Service Configuration**:
- Replicas: 1 per service (except frontend/backend: 2)
- Resource limits: Minimal (256Mi RAM per service)
- Autoscaling: Disabled
- Monitoring: Basic (kubectl logs, port-forward)

**Helm Values** (`values-local.yaml`):
```yaml
environment: local

# Replicas
frontend:
  replicaCount: 2
backend:
  replicaCount: 2
reminderService:
  replicaCount: 1
notificationService:
  replicaCount: 1
auditService:
  replicaCount: 1

# Resources (minimal for local)
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

# Kafka (single broker)
kafka:
  enabled: true
  replicaCount: 1
  persistence:
    enabled: false

# Dapr PubSub (Redis for simplicity)
dapr:
  pubsub:
    type: redis
    redis:
      host: redis-master.todo-app.svc.cluster.local

# Ingress
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: todo.local
      paths:
        - path: /
          service: frontend
    - host: api.todo.local
      paths:
        - path: /
          service: backend
  tls: []  # No TLS for local

# Autoscaling
autoscaling:
  enabled: false

# Monitoring
monitoring:
  enabled: false
```

**Deployment Command**:
```bash
# Start Minikube
minikube start --cpus=4 --memory=8192 --driver=docker

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server

# Install Dapr
helm install dapr dapr/dapr --namespace dapr-system --create-namespace

# Install Redis (for Dapr PubSub)
helm install redis bitnami/redis --namespace todo-app --create-namespace

# Deploy application
helm install todo-app ./helm/todo-app \
  --namespace todo-app \
  --create-namespace \
  -f helm/todo-app/values-local.yaml

# Configure DNS
echo "$(minikube ip) todo.local api.todo.local" | sudo tee -a /etc/hosts
```

---

### Cloud Kubernetes (Production)

**Purpose**: Production workloads, high availability, scalability

**Target Platforms**:
- Google Kubernetes Engine (GKE)
- Amazon Elastic Kubernetes Service (EKS)
- Azure Kubernetes Service (AKS)

**Infrastructure**:
- Multi-node cluster (minimum 3 nodes across 2 zones)
- Kafka: 3-broker cluster (Confluent Cloud or Strimzi Operator)
- Dapr PubSub: Kafka (durable, scalable)
- PostgreSQL: Managed service with read replicas (Cloud SQL, RDS, Azure Database)
- Ingress: Cloud Load Balancer (ALB, GLB, Azure Load Balancer)
- TLS: Let's Encrypt or cloud-managed certificates
- Monitoring: Prometheus + Grafana stack
- Logging: Centralized (Loki, ELK, or cloud logging)

**Service Configuration**:
- Replicas: 2-3 per service (HA)
- Resource limits: Production (512Mi-2Gi RAM per service)
- Autoscaling: HPA enabled (CPU/memory targets)
- Monitoring: Full observability stack

**Helm Values** (`values-production.yaml`):
```yaml
environment: production

# Replicas (HA)
frontend:
  replicaCount: 3
backend:
  replicaCount: 3
reminderService:
  replicaCount: 2  # Multiple replicas require leader election (future)
notificationService:
  replicaCount: 3
auditService:
  replicaCount: 2

# Resources (production sizing)
frontend:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 512Mi

backend:
  resources:
    requests:
      cpu: 300m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 1Gi

reminderService:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 512Mi

notificationService:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 512Mi

auditService:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi

# Kafka (managed service)
kafka:
  enabled: false  # Use external Confluent Cloud
  external:
    brokers: "pkc-xyz.us-west-2.aws.confluent.cloud:9092"
    saslMechanism: PLAIN
    saslUsername: <from-secret>
    saslPassword: <from-secret>

# Dapr PubSub (Kafka)
dapr:
  pubsub:
    type: kafka
    kafka:
      brokers: "pkc-xyz.us-west-2.aws.confluent.cloud:9092"
      authType: "sasl_plaintext"

# Ingress (with TLS)
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: todo.example.com
      paths:
        - path: /
          service: frontend
    - host: api.todo.example.com
      paths:
        - path: /
          service: backend
  tls:
    - secretName: todo-tls-cert
      hosts:
        - todo.example.com
        - api.todo.example.com

# Autoscaling (HPA)
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Monitoring
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

**Deployment Command**:
```bash
# Connect to cloud cluster
gcloud container clusters get-credentials todo-cluster --region=us-west1  # GKE
# OR
aws eks update-kubeconfig --name todo-cluster --region us-west-2  # EKS
# OR
az aks get-credentials --resource-group todo-rg --name todo-cluster  # AKS

# Install Dapr
helm install dapr dapr/dapr --namespace dapr-system --create-namespace

# Install Kafka (if not using managed service)
helm install kafka strimzi/strimzi-kafka-operator --namespace kafka --create-namespace

# Install monitoring stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Deploy application
helm install todo-app ./helm/todo-app \
  --namespace todo-app \
  --create-namespace \
  -f helm/todo-app/values-production.yaml

# Configure DNS (via cloud DNS service)
# Point todo.example.com and api.todo.example.com to Load Balancer IP
```

---

## Sequence Diagrams

### Sequence 1: Task Creation with Reminder

```
User          Frontend       Backend API      Dapr         Kafka        Reminder Svc    Audit Svc
 |                |               |              |            |                |            |
 |---POST /tasks->|               |              |            |                |            |
 |                |               |              |            |                |            |
 |                |--POST /api/tasks------------>|            |                |            |
 |                |               |              |            |                |            |
 |                |               |--1. Save task to DB       |                |            |
 |                |               |              |            |                |            |
 |                |               |--2. POST /v1.0/publish/-->|                |            |
 |                |               |       tasks.task.created  |                |            |
 |                |               |              |            |                |            |
 |                |               |              |--3. Write to Kafka Topic--->|            |
 |                |               |              |            |                |            |
 |                |               |              |            |                |            |
 |                |<--200 OK (task created)------|            |                |            |
 |                |               |              |            |                |            |
 |<--Task Created-|               |              |            |                |            |
 |                |               |              |            |                |            |
 |                |               |              |            |--4. Consume event---------->|
 |                |               |              |            |                |            |
 |                |               |              |            |                |--5. Persist event to DB
 |                |               |              |            |                |            |
 |                |               |              |            |--6. Consume event (if reminder_time set)
 |                |               |              |            |                |            |
 |                |               |              |            |                |--7. Schedule reminder in APScheduler
 |                |               |              |            |                |            |
 |                |               |              |            |                |--8. Save reminder to DB
 |                |               |              |            |                |            |
 |                |               |              |            |                |--9. Publish reminder.scheduled event
 |                |               |              |            |                |            |
 |                |               |              |            |<--reminder.scheduled event--|
 |                |               |              |            |                |            |
 |                |               |              |            |--10. Consume event--------->|
 |                |               |              |            |                |            |
 |                |               |              |            |                |--11. Persist event to DB
```

**Flow Explanation**:
1. User submits task creation form via frontend
2. Frontend sends POST request to Backend API
3. Backend API saves task to PostgreSQL database
4. Backend API publishes `tasks.task.created` event to Dapr
5. Dapr writes event to Kafka topic
6. Backend API returns success response to frontend
7. Kafka delivers event to Reminder Service (subscriber)
8. Kafka delivers event to Audit Service (subscriber)
9. Audit Service persists event to `events` table
10. Reminder Service checks if task has `reminder_time`
11. If reminder present, Reminder Service schedules job in APScheduler
12. Reminder Service saves reminder record to `reminders` table
13. Reminder Service publishes `reminders.reminder.scheduled` event
14. Audit Service consumes and persists the reminder scheduled event

**Timing**: Entire flow completes in <500ms (async event processing in background)

---

### Sequence 2: Reminder Firing and Notification

```
APScheduler   Reminder Svc    Dapr        Kafka     Notification Svc   SendGrid    Audit Svc
    |             |             |           |              |                |           |
    |--1. Trigger reminder job->|           |              |                |           |
    |             |             |           |              |                |           |
    |             |--2. Publish reminder.fired event----->|              |                |           |
    |             |             |           |              |                |           |
    |             |             |--3. Write to Kafka------>|              |                |           |
    |             |             |           |              |                |           |
    |             |--4. Update reminder status (fired)     |              |                |           |
    |             |             |           |              |                |           |
    |             |             |           |--5. Consume event------------>|                |           |
    |             |             |           |              |                |           |
    |             |             |           |              |--6. Fetch user preferences (email, webhook)
    |             |             |           |              |                |           |
    |             |             |           |              |--7. Render email template
    |             |             |           |              |                |           |
    |             |             |           |              |--8. Send email via API----->|           |
    |             |             |           |              |                |           |
    |             |             |           |              |<--9. 200 OK (email sent)----|           |
    |             |             |           |              |                |           |
    |             |             |           |              |--10. Save notification history (DB)
    |             |             |           |              |                |           |
    |             |             |           |--11. Consume event (Audit)--------------->|
    |             |             |           |              |                |           |
    |             |             |           |              |                |--12. Persist event to DB
```

**Flow Explanation**:
1. APScheduler triggers reminder job at scheduled time (e.g., 5:00 PM)
2. Reminder Service publishes `reminders.reminder.fired` event to Dapr
3. Dapr writes event to Kafka topic
4. Reminder Service updates reminder status to 'fired' in database
5. Kafka delivers event to Notification Service (subscriber)
6. Notification Service fetches user preferences (email, webhook URL)
7. Notification Service renders email template with task details
8. Notification Service sends email via SendGrid API
9. SendGrid returns success response
10. Notification Service saves notification history to database
11. Kafka delivers event to Audit Service (subscriber)
12. Audit Service persists event to `events` table

**Timing**: Reminder fires within 1 minute of scheduled time, notification delivery within 5 seconds

---

### Sequence 3: Recurring Task Generation

```
K8s CronJob   Recurring Gen   PostgreSQL     Dapr        Kafka      Reminder Svc   Audit Svc
    |             |               |            |           |              |            |
    |--1. Trigger job (2 AM UTC)->|            |           |              |            |
    |             |               |            |           |              |            |
    |             |--2. Query recurrence_patterns--------->|              |            |
    |             |               |            |           |              |            |
    |             |<--3. Return patterns (100 records)-----|              |            |
    |             |               |            |           |              |            |
    |             |--4. For each pattern, calculate next 30 days instances            |
    |             |               |            |           |              |            |
    |             |--5. Save task instances to DB--------->|              |            |
    |             |               |            |           |              |            |
    |             |--6. For each instance, publish event-->|              |            |
    |             |               |            |           |              |            |
    |             |               |            |--7. Write to Kafka------>|            |
    |             |               |            |           |              |            |
    |             |               |            |           |--8. Consume event (Reminder Svc)
    |             |               |            |           |              |            |
    |             |               |            |           |              |--9. Schedule reminders
    |             |               |            |           |              |            |
    |             |               |            |           |--10. Consume event (Audit Svc)
    |             |               |            |           |              |            |
    |             |               |            |           |              |--11. Persist event
    |             |               |            |           |              |            |
    |             |--12. Update pattern last_generated_at->|              |            |
    |             |               |            |           |              |            |
    |<--13. Job complete----------|            |           |              |            |
```

**Flow Explanation**:
1. Kubernetes CronJob triggers at 2:00 AM UTC daily
2. Recurring Task Generator queries `recurrence_patterns` table for active patterns
3. Database returns patterns needing new instances (e.g., 100 patterns)
4. Generator calculates task instances for next 30 days for each pattern
5. Generator saves all task instances to `tasks` table (bulk insert)
6. For each instance, generator publishes `recurring.instance.generated` event
7. Dapr writes events to Kafka (batched for performance)
8. Reminder Service consumes events and schedules reminders for instances
9. Audit Service consumes events and persists to `events` table
10. Generator updates `last_generated_at` timestamp on patterns
11. CronJob completes (pod terminates)

**Timing**: Job runs for 2-15 minutes depending on number of patterns (thousands of patterns)

---

## Data Architecture

### Database Schema Extensions

#### Table: `tasks` (Extended from Phase II)

**New Columns**:
```sql
-- Phase V extensions to tasks table
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP NULL;
ALTER TABLE tasks ADD COLUMN reminder_time TIMESTAMP NULL;
ALTER TABLE tasks ADD COLUMN reminder_config JSONB NULL;
ALTER TABLE tasks ADD COLUMN recurrence_pattern_id UUID NULL;
ALTER TABLE tasks ADD COLUMN recurrence_instance_id UUID NULL;
ALTER TABLE tasks ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE;

-- Index for queries
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_recurrence_pattern ON tasks(recurrence_pattern_id) WHERE recurrence_pattern_id IS NOT NULL;
```

**Reminder Config Schema** (JSONB):
```json
{
  "channels": ["email", "in_app", "webhook"],
  "webhook_url": "https://example.com/webhook",
  "advance_notice_minutes": 60
}
```

#### Table: `recurrence_patterns` (New)

```sql
CREATE TABLE recurrence_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_template JSONB NOT NULL,  -- Template for task creation
    frequency VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'yearly', 'custom'
    interval INTEGER NOT NULL DEFAULT 1,  -- Every N days/weeks/months
    days_of_week INTEGER[],  -- For weekly: [0=Mon, 1=Tue, ..., 6=Sun]
    day_of_month INTEGER,  -- For monthly: 1-31 or -1 (last day)
    end_date TIMESTAMP NULL,  -- When to stop generating
    max_occurrences INTEGER NULL,  -- Max number of instances
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    last_generated_at TIMESTAMP NULL,  -- Last time instances were generated
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CHECK (frequency IN ('daily', 'weekly', 'monthly', 'yearly', 'custom')),
    CHECK (interval > 0),
    CHECK (end_date IS NULL OR max_occurrences IS NULL)  -- Only one end condition
);

CREATE INDEX idx_recurrence_user ON recurrence_patterns(user_id);
CREATE INDEX idx_recurrence_last_generated ON recurrence_patterns(last_generated_at);
```

**Task Template Schema** (JSONB):
```json
{
  "title": "Weekly team meeting",
  "description": "Discuss project updates",
  "priority": "medium",
  "reminder_minutes_before": 15
}
```

#### Table: `reminders` (New)

```sql
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'fired', 'cancelled'
    notification_channels JSONB NOT NULL,  -- ["email", "in_app"]
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    fired_at TIMESTAMP NULL,

    CHECK (status IN ('pending', 'fired', 'cancelled'))
);

CREATE INDEX idx_reminders_task ON reminders(task_id);
CREATE INDEX idx_reminders_user ON reminders(user_id);
CREATE INDEX idx_reminders_scheduled ON reminders(scheduled_time) WHERE status = 'pending';
CREATE INDEX idx_reminders_status ON reminders(status);
```

#### Table: `events` (New, for Audit Service)

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,  -- 'tasks.task.created', etc.
    aggregate_id UUID NOT NULL,  -- task_id, reminder_id, etc.
    user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    payload JSONB NOT NULL,  -- Full CloudEvent
    metadata JSONB NULL,  -- Additional metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_aggregate ON events(aggregate_id);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_created ON events(created_at DESC);

-- Partition table by month for performance (production)
-- CREATE TABLE events_202601 PARTITION OF events FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

#### Table: `notifications` (New, for Notification Service)

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_id UUID NULL REFERENCES reminders(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL,  -- 'email', 'in_app', 'webhook'
    recipient VARCHAR(255) NOT NULL,  -- email address or webhook URL
    subject VARCHAR(255) NULL,
    body TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'sent', 'failed'
    error_message TEXT NULL,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CHECK (channel IN ('email', 'in_app', 'webhook')),
    CHECK (status IN ('pending', 'sent', 'failed'))
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

#### Table: `apscheduler_jobs` (New, APScheduler State)

APScheduler automatically creates this table for persistent job storage:

```sql
CREATE TABLE apscheduler_jobs (
    id VARCHAR(191) PRIMARY KEY,
    next_run_time DOUBLE PRECISION NULL,
    job_state BYTEA NOT NULL
);

CREATE INDEX idx_apscheduler_next_run ON apscheduler_jobs(next_run_time);
```

### Database Migration Strategy

**Migration Tool**: Alembic (Python database migration tool)

**Migration Files**:
```
backend/alembic/versions/
├── 001_phase2_initial.py          # Phase II tables (users, tasks)
├── 002_phase3_ai_chat.py           # Phase III extensions (if any)
└── 003_phase5_event_driven.py     # Phase V tables (NEW)
```

**Migration 003 (Phase V)**:
```python
# backend/alembic/versions/003_phase5_event_driven.py

"""Phase V: Event-driven architecture tables

Revision ID: 003
Revises: 002
Create Date: 2026-01-08
"""

def upgrade():
    # Extend tasks table
    op.add_column('tasks', sa.Column('due_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('tasks', sa.Column('reminder_time', sa.TIMESTAMP(), nullable=True))
    op.add_column('tasks', sa.Column('reminder_config', sa.JSON(), nullable=True))
    op.add_column('tasks', sa.Column('recurrence_pattern_id', sa.UUID(), nullable=True))
    op.add_column('tasks', sa.Column('recurrence_instance_id', sa.UUID(), nullable=True))
    op.add_column('tasks', sa.Column('is_recurring', sa.Boolean(), server_default='false'))

    # Create recurrence_patterns table
    op.create_table('recurrence_patterns', ...)

    # Create reminders table
    op.create_table('reminders', ...)

    # Create events table
    op.create_table('events', ...)

    # Create notifications table
    op.create_table('notifications', ...)

    # Create indexes
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    # ... etc

def downgrade():
    # Reverse all changes
    op.drop_table('notifications')
    op.drop_table('events')
    op.drop_table('reminders')
    op.drop_table('recurrence_patterns')
    op.drop_column('tasks', 'is_recurring')
    # ... etc
```

**Deployment**: Run migrations as init container in Backend API deployment

---

## Security Architecture

### Authentication & Authorization (Unchanged)

- JWT tokens in httpOnly cookies (Phase II/III)
- User isolation via `user_id` foreign keys
- Password hashing with bcrypt

### Event Security

**Event Payload Encryption** (Optional, future):
- Encrypt sensitive fields in event payloads (e.g., email addresses)
- Use envelope encryption (data key encrypted by master key)

**Event Authentication**:
- All events signed with HMAC (future enhancement)
- Verify event authenticity in consumers

### Kafka Security

**Local (Minikube)**:
- No authentication (trusted network)
- Kafka runs inside cluster (not exposed externally)

**Production**:
- SASL/SCRAM authentication (username/password)
- SSL/TLS encryption in transit
- ACLs to restrict topic access per service

**Configuration** (Production):
```yaml
# Dapr Kafka component with SASL/SSL
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka-broker:9093"
  - name: authType
    value: "password"
  - name: saslUsername
    secretKeyRef:
      name: kafka-credentials
      key: username
  - name: saslPassword
    secretKeyRef:
      name: kafka-credentials
      key: password
  - name: saslMechanism
    value: "SCRAM-SHA-512"
  - name: enableTLS
    value: "true"
```

### Secrets Management

**Local (Minikube)**:
- Kubernetes Secrets (base64 encoded)
- Secret values in `values-local.yaml` (not committed to git)

**Production**:
- External Secrets Operator + Cloud Secret Manager
- Secrets rotated automatically (90-day policy)

**Secrets**:
- Database connection string (PostgreSQL)
- JWT signing key
- Kafka credentials (SASL username/password)
- SendGrid API key
- OpenAI API key (Phase III)

### Network Policies (Production)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-api-policy
  namespace: todo-app
spec:
  podSelector:
    matchLabels:
      app: backend-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: dapr-system
```

---

## Observability Architecture

### Metrics

**Prometheus Metrics** (exposed by all services on `:9090/metrics`):

**Backend API**:
- `http_requests_total{method, path, status}` - Total HTTP requests
- `http_request_duration_seconds{method, path}` - Request latency histogram
- `tasks_created_total` - Total tasks created
- `events_published_total{topic}` - Total events published

**Reminder Service**:
- `reminders_scheduled_total` - Total reminders scheduled
- `reminders_fired_total` - Total reminders fired
- `reminder_firing_lag_seconds` - Difference between scheduled and actual firing time

**Notification Service**:
- `notifications_sent_total{channel, status}` - Total notifications sent
- `notification_delivery_duration_seconds{channel}` - Delivery latency

**Audit Service**:
- `events_persisted_total{event_type}` - Total events persisted

**Dapr Metrics** (built-in):
- `dapr_component_pubsub_egress_count{topic, status}` - Messages published
- `dapr_component_pubsub_ingress_count{topic, status}` - Messages received

### Logging

**Structured Logging** (JSON format):

```json
{
  "timestamp": "2026-01-08T12:34:56Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task created",
  "task_id": "123",
  "user_id": "456",
  "event_published": true
}
```

**Log Aggregation**:
- Local: `kubectl logs` (ephemeral)
- Production: Loki or ELK stack or cloud logging (GCP Logging, CloudWatch, Azure Monitor)

### Distributed Tracing

**Dapr Tracing** (OpenTelemetry):
- Trace context propagated automatically via Dapr sidecars
- Spans created for:
  - HTTP requests to services
  - Event publishing (Dapr → Kafka)
  - Event consumption (Kafka → Dapr → Service)

**Trace Collector**: Jaeger or Zipkin

**Configuration** (Dapr tracing config):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: tracing
  namespace: todo-app
spec:
  tracing:
    samplingRate: "1"  # 100% sampling (reduce in production)
    zipkin:
      endpointAddress: "http://zipkin.monitoring.svc.cluster.local:9411/api/v2/spans"
```

### Dashboards

**Grafana Dashboards**:
1. **Application Overview**
   - Request rate, latency, error rate (RED metrics)
   - Task creation rate
   - Event publishing rate

2. **Event Processing**
   - Kafka topic lag per consumer
   - Event consumption rate
   - Event processing errors

3. **Reminders**
   - Reminders scheduled vs fired
   - Reminder firing accuracy (lag distribution)
   - Failed reminders

4. **Notifications**
   - Notifications sent per channel
   - Delivery success rate
   - Delivery latency

5. **Infrastructure**
   - Kafka broker metrics (throughput, storage)
   - Dapr sidecar metrics (latency, errors)
   - Database connection pool usage

---

## Validation Strategy

### Pre-Deployment Validation

1. **Static Analysis**
   - Helm chart linting: `helm lint ./helm/todo-app`
   - Kubernetes manifest validation: `kubeval k8s/*.yaml`
   - Python linting: `pylint`, `mypy`

2. **Security Scanning**
   - Docker image scanning: `trivy image todo-backend:latest`
   - Dependency scanning: `safety check` (Python), `npm audit` (Node.js)
   - Secret scanning: `detect-secrets` (prevent committed secrets)

3. **Unit Tests**
   - Backend API: `pytest backend/tests/` (target: 80% coverage)
   - Services: Unit tests for event handlers, business logic

4. **Integration Tests**
   - Database integration tests (test against test database)
   - Dapr PubSub integration tests (mock Kafka)

### Post-Deployment Validation

1. **Smoke Tests** (automated in CI/CD):
   ```bash
   # Health checks
   curl https://api.todo.example.com/health
   curl https://todo.example.com/

   # Functional tests
   # 1. Create user
   # 2. Create task
   # 3. Verify task appears in list
   # 4. Create recurring pattern
   # 5. Verify pattern saved
   ```

2. **End-to-End Tests** (Playwright/Cypress):
   - User registration → task creation → reminder scheduling
   - Recurring pattern creation → verify instances generated
   - Notification delivery verification (email sandbox)

3. **Performance Tests** (k6 or Locust):
   - Task creation throughput (target: 100 req/sec)
   - Event processing lag (target: <1 second p95)
   - Reminder firing accuracy (target: within 1 minute)

4. **Chaos Tests** (optional, production):
   - Kill Kafka broker (verify message replay)
   - Kill reminder service pod (verify scheduler state recovery)
   - Simulate network partition (verify Dapr retries)

### Monitoring and Alerting

**Alerts** (PagerDuty, Slack, email):

1. **Critical**:
   - Service down (all replicas unhealthy)
   - Database connection failure
   - Kafka broker down
   - Reminder firing lag >5 minutes

2. **Warning**:
   - High error rate (>5% of requests)
   - High event processing lag (>1 minute)
   - Disk usage >80% (Kafka brokers)
   - Memory usage >90%

3. **Info**:
   - Deployment completed
   - Auto-scaling event (HPA triggered)
   - Certificate expiration warning (30 days)

---

## Risk Mitigation

### Risk 1: Kafka Operational Complexity

**Impact**: High | **Probability**: Medium

**Mitigation**:
- Use managed Kafka service in production (Confluent Cloud, AWS MSK)
- Comprehensive runbooks for common operations (topic creation, consumer lag investigation)
- Monitoring and alerting for broker health
- Local development uses Redis (simpler alternative)

### Risk 2: Event Ordering Issues

**Impact**: High | **Probability**: Low

**Mitigation**:
- Partition tasks topics by `user_id` (guarantees ordering per user)
- Idempotent event handlers (safe to replay)
- Document ordering guarantees in event schemas
- Testing with out-of-order events

### Risk 3: Reminder Accuracy at Scale

**Impact**: High | **Probability**: Medium

**Mitigation**:
- APScheduler with PostgreSQL JobStore (persistent state)
- Monitoring reminder firing lag
- Load testing with 100,000+ reminders
- Graceful degradation if scheduler overloaded

### Risk 4: Database Bottleneck (Shared Database)

**Impact**: Medium | **Probability**: Medium

**Mitigation**:
- Connection pooling (limit concurrent connections)
- Read replicas for analytics/audit queries (future)
- Database indexes optimized for common queries
- Plan migration to per-service databases (Phase VI)

### Risk 5: Dapr Learning Curve

**Impact**: Medium | **Probability**: High

**Mitigation**:
- Comprehensive documentation with examples
- Reference Dapr quickstarts and samples
- Start simple (PubSub only), expand later (State Store, Bindings)
- Training sessions for team

### Risk 6: Cloud Cost Overruns

**Impact**: Medium | **Probability**: Medium

**Mitigation**:
- Budget alerts (GCP/AWS/Azure billing alerts)
- Resource limits on all pods (prevent runaway scaling)
- Auto-scaling limits (max 10 replicas per service)
- Cost optimization reviews monthly

### Risk 7: CI/CD Pipeline Failures

**Impact**: Low | **Probability**: Low

**Mitigation**:
- Automated rollback on deployment failure
- Smoke tests catch deployment issues early
- Manual approval gate for production
- Blue-green deployments (zero downtime)

---

## Success Criteria

Phase V is complete when:

### Functional Criteria

1. **Event-Driven Architecture**
   - ✅ All task operations publish events to Kafka
   - ✅ Minimum 3 event consumers operational (Reminder, Notification, Audit)
   - ✅ Events persisted to `events` table
   - ✅ Event replay capability demonstrated

2. **Task Reminders**
   - ✅ Users can set due dates and reminders via UI
   - ✅ Reminders fire within 1 minute of scheduled time (p95)
   - ✅ Notifications delivered via email (SendGrid integration)
   - ✅ In-app notifications displayed (WebSocket or polling)

3. **Recurring Tasks**
   - ✅ Users can create recurring patterns (daily, weekly, monthly)
   - ✅ Task instances auto-generated daily by CronJob
   - ✅ Instances appear in task list with "recurring" indicator
   - ✅ Users can modify or delete individual instances

4. **Dapr Integration**
   - ✅ Dapr deployed to Minikube and cloud clusters
   - ✅ Kafka configured as PubSub component (production)
   - ✅ Redis configured as PubSub component (local)
   - ✅ All services communicate via Dapr APIs (no direct Kafka clients)

5. **Local Deployment**
   - ✅ Minikube deployment updated with all Phase V components
   - ✅ One-command deployment script (`./deploy-local.sh`)
   - ✅ Validation script covers new services
   - ✅ Documentation updated

6. **Cloud Deployment**
   - ✅ Production deployment on GKE, EKS, or AKS
   - ✅ TLS/HTTPS enabled with valid certificates
   - ✅ Auto-scaling operational (HPA)
   - ✅ Monitoring dashboards configured (Grafana)
   - ✅ Centralized logging operational

7. **CI/CD Pipeline**
   - ✅ Automated builds on every commit (GitHub Actions)
   - ✅ Automated tests (unit, integration, e2e) pass
   - ✅ Automated deployment to dev/staging environments
   - ✅ Manual approval for production deployment
   - ✅ Automated rollback on failure
   - ✅ Pipeline execution time <15 minutes

### Non-Functional Criteria

8. **Performance**
   - ✅ Task creation API: <200ms p95 latency
   - ✅ Event publishing: <100ms overhead
   - ✅ Event processing lag: <1 second p95
   - ✅ Reminder firing accuracy: within 1 minute p95

9. **Reliability**
   - ✅ Service uptime: >99% (staging), >99.9% (production)
   - ✅ Zero data loss (events persisted to Kafka)
   - ✅ Graceful handling of Kafka/Dapr failures

10. **Scalability**
    - ✅ System handles 1000+ events per second
    - ✅ System supports 100,000+ active reminders
    - ✅ System supports 10,000+ recurring patterns
    - ✅ Auto-scaling maintains performance under load

11. **Security**
    - ✅ Kafka authentication enabled (production)
    - ✅ Secrets managed via External Secrets Operator (production)
    - ✅ Network policies restrict inter-service communication (production)
    - ✅ No secrets committed to git

12. **Observability**
    - ✅ Prometheus metrics for all services
    - ✅ Distributed tracing operational (Jaeger/Zipkin)
    - ✅ Centralized logging operational
    - ✅ Grafana dashboards for key metrics
    - ✅ Alerts configured for critical failures

13. **Documentation**
    - ✅ Architecture documentation complete
    - ✅ Deployment runbooks updated (local and cloud)
    - ✅ API documentation updated (OpenAPI)
    - ✅ User guide for reminders and recurring tasks

14. **Testing**
    - ✅ Unit test coverage >80%
    - ✅ Integration tests pass
    - ✅ End-to-end tests pass
    - ✅ Performance tests meet SLAs

---

## Next Steps

After approval of this plan:

1. **Generate Tasks** (`/sp.tasks`):
   - Break down implementation into atomic tasks
   - Assign tasks to implementation phases
   - Define acceptance criteria per task

2. **Implementation Phases**:
   - **Phase 1**: Database migrations and schema extensions
   - **Phase 2**: Backend API extensions (recurring patterns, reminders API)
   - **Phase 3**: Kafka and Dapr setup (local and cloud)
   - **Phase 4**: Reminder Service implementation
   - **Phase 5**: Notification Service implementation
   - **Phase 6**: Audit Service implementation
   - **Phase 7**: Recurring Task Generator implementation
   - **Phase 8**: Frontend UI updates
   - **Phase 9**: CI/CD pipeline implementation
   - **Phase 10**: Cloud deployment and production readiness

3. **Documentation**:
   - Deployment runbook updates
   - Architecture diagrams (detailed)
   - API documentation updates
   - User guide for new features

---

**End of Plan**
