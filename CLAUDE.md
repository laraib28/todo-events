# Todo Events - Phase 5

Event-driven architecture with Dapr, Kafka pub/sub, recurring tasks, and reminders.

## Quick Start

### Local Development
```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd backend && python run_reminder_worker.py  # separate terminal
cd frontend && npm install && npm run dev
```

### Kubernetes with Dapr + Kafka
```bash
minikube start
bash k8s/dapr-install.sh
bash k8s/kafka/install-kafka-local.sh
kubectl apply -f k8s/dapr-components/
kubectl apply -f k8s/
```

## Architecture
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + AI + Events
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS
- **Events**: Dapr pub/sub with Kafka broker
- **Workers**: Background reminder worker
- **K8s**: Full deployment with Dapr sidecars

## Key Components
- `backend/app/events/` - Event publishing with Dapr
- `backend/app/workers/` - Background reminder processing
- `backend/app/routers/recurring.py` - Recurring task endpoints
- `backend/app/routers/reminders.py` - Reminder endpoints
- `k8s/dapr-components/` - Dapr component configs
- `k8s/kafka/` - Kafka setup scripts
