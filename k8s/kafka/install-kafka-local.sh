#!/bin/bash
# Install Kafka for Local (Minikube) Development
#
# Task: T-543 - Create k8s/kafka/install-kafka-local.sh
# Phase: Phase V - Event-Driven Architecture
#
# This script installs Apache Kafka using the Bitnami Helm chart
# with settings optimized for local Minikube development.
#
# Prerequisites:
#   - Minikube running (minikube status)
#   - Helm 3 installed (helm version)
#   - kubectl configured (kubectl cluster-info)
#
# Usage:
#   ./install-kafka-local.sh
#
# This script will:
#   1. Add Bitnami Helm repository
#   2. Create todo-app namespace if not exists
#   3. Install Kafka with local values
#   4. Wait for Kafka to be ready
#   5. Verify installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="todo-app"
RELEASE_NAME="kafka"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}=== Phase V: Installing Kafka for Local Development ===${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"

# Add Bitnami Helm repository
echo -e "${YELLOW}Adding Bitnami Helm repository...${NC}"
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update

# Create namespace if not exists
echo -e "${YELLOW}Creating namespace ${NAMESPACE}...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Check if Kafka is already installed
if helm status ${RELEASE_NAME} -n ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}Kafka is already installed. Upgrading...${NC}"
    ACTION="upgrade"
else
    echo -e "${YELLOW}Installing Kafka...${NC}"
    ACTION="install"
fi

# Install/Upgrade Kafka
helm ${ACTION} ${RELEASE_NAME} bitnami/kafka \
    --namespace ${NAMESPACE} \
    --values "${SCRIPT_DIR}/values-local.yaml" \
    --wait \
    --timeout 5m

# Verify installation
echo -e "${YELLOW}Verifying Kafka installation...${NC}"

# Wait for pods to be ready
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=kafka \
    -n ${NAMESPACE} \
    --timeout=120s

# Display status
echo -e "${GREEN}=== Kafka Installation Complete ===${NC}"
echo ""
echo "Kafka Broker Service: kafka.${NAMESPACE}.svc.cluster.local:9092"
echo ""
echo "To test Kafka, run:"
echo "  kubectl exec -it kafka-controller-0 -n ${NAMESPACE} -- kafka-topics.sh --list --bootstrap-server localhost:9092"
echo ""
echo "To create Phase V topics, run:"
echo "  ./create-topics.sh"
