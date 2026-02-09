# Todo Events - Phase 5

Event-driven Todo application with Dapr pub/sub, Kafka messaging, recurring tasks, and reminders.

## Features
- Everything from Phase 4 (web app, AI, K8s, Helm)
- Event-driven architecture with Dapr
- Kafka pub/sub for async messaging
- Recurring tasks with cron scheduling
- Reminder system with background worker

## Tech Stack
- **App**: FastAPI + Next.js 16 + PostgreSQL + OpenAI
- **Events**: Dapr pub/sub framework
- **Messaging**: Apache Kafka
- **Workers**: Background reminder processor
- **Containers**: Docker + Kubernetes + Helm

## Quick Start

### Local Development
```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd backend && python run_reminder_worker.py  # separate terminal
cd frontend && npm install && npm run dev
```

### Kubernetes + Dapr + Kafka
```bash
minikube start && minikube addons enable ingress
bash k8s/dapr-install.sh
bash k8s/kafka/install-kafka-local.sh
kubectl apply -f k8s/dapr-components/
kubectl apply -f k8s/
```

## Project Structure
```
backend/
├── app/
│   ├── ai/              # AI agent
│   ├── mcp/             # MCP tools
│   ├── events/          # Event publishing
│   ├── workers/         # Background workers
│   ├── routers/
│   │   ├── recurring.py # Recurring tasks
│   │   └── reminders.py # Reminders
k8s/
├── dapr-components/     # Dapr pub/sub configs
├── kafka/               # Kafka setup
helm/todo-app/
```

## Built with Claude Code + SpecKit
