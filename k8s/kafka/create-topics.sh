#!/bin/bash
# Create Kafka Topics for Phase V Event-Driven Architecture
#
# Task: T-544 - Create k8s/kafka/create-topics.sh
# Phase: Phase V - Event-Driven Architecture
#
# This script creates the required Kafka topics for the Phase V
# event-driven architecture with proper partition and retention settings.
#
# Topics created:
#   - tasks.task.created       (task creation events)
#   - tasks.task.updated       (task update events)
#   - tasks.task.completed     (task completion events)
#   - tasks.task.deleted       (task deletion events)
#   - reminders.reminder.scheduled (reminder scheduling events)
#   - reminders.reminder.fired     (reminder firing events)
#   - reminders.reminder.cancelled (reminder cancellation events)
#   - recurring.instance.generated (recurring task generation events)
#
# Usage:
#   ./create-topics.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="todo-app"
KAFKA_POD="kafka-controller-0"
BOOTSTRAP_SERVER="localhost:9092"

# Topic configuration
PARTITIONS=3
REPLICATION_FACTOR=1
RETENTION_MS=$((7 * 24 * 60 * 60 * 1000))  # 7 days in milliseconds

# Topics to create (following naming convention: {domain}.{entity}.{event})
TOPICS=(
    "tasks.task.created"
    "tasks.task.updated"
    "tasks.task.completed"
    "tasks.task.deleted"
    "reminders.reminder.scheduled"
    "reminders.reminder.fired"
    "reminders.reminder.cancelled"
    "recurring.instance.generated"
)

echo -e "${GREEN}=== Phase V: Creating Kafka Topics ===${NC}"

# Check if Kafka pod is ready
echo -e "${YELLOW}Checking Kafka availability...${NC}"
if ! kubectl get pod ${KAFKA_POD} -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}Error: Kafka pod ${KAFKA_POD} not found in namespace ${NAMESPACE}${NC}"
    echo "Please run ./install-kafka-local.sh first"
    exit 1
fi

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod/${KAFKA_POD} -n ${NAMESPACE} --timeout=60s

# Create topics
echo -e "${YELLOW}Creating topics with ${PARTITIONS} partitions and ${RETENTION_MS}ms retention...${NC}"

for TOPIC in "${TOPICS[@]}"; do
    echo -e "  Creating topic: ${TOPIC}"
    kubectl exec ${KAFKA_POD} -n ${NAMESPACE} -- \
        kafka-topics.sh --create \
        --bootstrap-server ${BOOTSTRAP_SERVER} \
        --topic "${TOPIC}" \
        --partitions ${PARTITIONS} \
        --replication-factor ${REPLICATION_FACTOR} \
        --config retention.ms=${RETENTION_MS} \
        --if-not-exists \
        2>/dev/null || echo "    (topic may already exist)"
done

# List all topics
echo -e "${GREEN}=== Topics Created ===${NC}"
kubectl exec ${KAFKA_POD} -n ${NAMESPACE} -- \
    kafka-topics.sh --list --bootstrap-server ${BOOTSTRAP_SERVER}

echo ""
echo -e "${GREEN}Topic creation complete!${NC}"
echo ""
echo "To view topic details, run:"
echo "  kubectl exec ${KAFKA_POD} -n ${NAMESPACE} -- kafka-topics.sh --describe --bootstrap-server ${BOOTSTRAP_SERVER}"
