#!/bin/bash
# Install Dapr Components for Local Development
#
# Task: T-553 - Create k8s/dapr-components/install-components-local.sh
# Phase: Phase V - Event-Driven Architecture
#
# This script installs:
#   1. Redis (as PubSub backend for local development)
#   2. Dapr PubSub component (pubsub-redis.yaml)
#
# For production, use Kafka instead (pubsub-kafka.yaml)
#
# Prerequisites:
#   - Kubernetes cluster running
#   - Dapr control plane installed (run dapr-install.sh first)
#   - Helm 3 installed
#
# Usage:
#   ./install-components-local.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="todo-app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}=== Phase V: Installing Dapr Components (Local) ===${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    exit 1
fi

if ! kubectl get namespace dapr-system &> /dev/null; then
    echo -e "${RED}Error: Dapr is not installed. Run dapr-install.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"

# Create namespace if not exists
echo -e "${YELLOW}Creating namespace ${NAMESPACE}...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Add Bitnami Helm repository
echo -e "${YELLOW}Adding Bitnami Helm repository...${NC}"
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update

# Install Redis for Dapr PubSub
echo -e "${YELLOW}Installing Redis...${NC}"
if helm status redis -n ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}Redis is already installed. Skipping...${NC}"
else
    helm install redis bitnami/redis \
        --namespace ${NAMESPACE} \
        --set architecture=standalone \
        --set auth.enabled=true \
        --set auth.password=todoapp-redis-password \
        --set master.persistence.enabled=false \
        --set master.resources.requests.cpu=100m \
        --set master.resources.requests.memory=128Mi \
        --set master.resources.limits.cpu=500m \
        --set master.resources.limits.memory=256Mi \
        --wait \
        --timeout 3m
fi

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=redis \
    -n ${NAMESPACE} \
    --timeout=120s

# Create Redis password secret for Dapr (if using different secret name)
echo -e "${YELLOW}Verifying Redis secret exists...${NC}"
if ! kubectl get secret redis -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}Error: Redis secret not found${NC}"
    exit 1
fi

# Apply Dapr PubSub component
echo -e "${YELLOW}Applying Dapr PubSub component (Redis)...${NC}"
kubectl apply -f "${SCRIPT_DIR}/pubsub-redis.yaml"

# Verify component
echo -e "${YELLOW}Verifying Dapr component...${NC}"
kubectl get component todo-pubsub -n ${NAMESPACE}

echo -e "${GREEN}=== Dapr Components Installation Complete ===${NC}"
echo ""
echo "Installed components:"
echo "  - Redis: redis-master.${NAMESPACE}.svc.cluster.local:6379"
echo "  - Dapr PubSub: todo-pubsub (Redis backend)"
echo ""
echo "To test the PubSub component:"
echo "  1. Deploy an app with Dapr annotations"
echo "  2. Publish events to topic via: POST http://localhost:3500/v1.0/publish/todo-pubsub/<topic>"
echo ""
echo "Next steps:"
echo "  1. Add Dapr annotations to backend deployment"
echo "  2. Update Backend API to publish events"
