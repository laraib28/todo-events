---
name: event-publishing
description: Dapr event publishing workflow
---

# Event Publishing with Dapr

## Event Types
- `task.created` - New task created
- `task.updated` - Task modified
- `task.completed` - Task marked complete
- `task.deleted` - Task removed
- `reminder.due` - Reminder is due
- `recurring.trigger` - Recurring task trigger

## Publishing Events
```python
from app.events.publisher import publish_event
await publish_event("task.created", {"task_id": task.id, "title": task.title})
```

## Dapr Components
- `k8s/dapr-components/pubsub-kafka.yaml` - Kafka pub/sub
- `k8s/dapr-components/pubsub-redis.yaml` - Redis pub/sub (local)

## Testing
```bash
dapr run --app-id todo-backend --app-port 8000 -- uvicorn app.main:app
```
