---
name: kafka-management
description: Kafka topic and broker management
---

# Kafka Management

## Install Kafka (Minikube)
```bash
bash k8s/kafka/install-kafka-local.sh
```

## Create Topics
```bash
bash k8s/kafka/create-topics.sh
```

## Troubleshooting
```bash
kubectl get pods -l app=kafka -n todo-app
kubectl logs -l app=kafka -n todo-app
```
