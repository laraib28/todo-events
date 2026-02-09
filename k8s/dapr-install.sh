#!/bin/bash
# Install Dapr Control Plane for Kubernetes
#
# Task: T-551 - Create k8s/dapr-install.sh
# Phase: Phase V - Event-Driven Architecture
#
# This script installs the Dapr control plane in a Kubernetes cluster
# using the official Dapr Helm chart.
#
# Dapr Components Installed:
#   - dapr-operator: Manages Dapr component resources
#   - dapr-sidecar-injector: Injects Dapr sidecars into pods
#   - dapr-placement: Provides actor placement service
#   - dapr-sentry: Provides mTLS and certificate management
#
# Prerequisites:
#   - Kubernetes cluster running (minikube or cloud)
#   - Helm 3 installed
#   - kubectl configured
#
# Usage:
#   ./dapr-install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DAPR_NAMESPACE="dapr-system"
DAPR_VERSION="1.12"  # Dapr version to install

echo -e "${GREEN}=== Phase V: Installing Dapr Control Plane ===${NC}"

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

# Add Dapr Helm repository
echo -e "${YELLOW}Adding Dapr Helm repository...${NC}"
helm repo add dapr https://dapr.github.io/helm-charts/ 2>/dev/null || true
helm repo update

# Create Dapr namespace
echo -e "${YELLOW}Creating namespace ${DAPR_NAMESPACE}...${NC}"
kubectl create namespace ${DAPR_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Check if Dapr is already installed
if helm status dapr -n ${DAPR_NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}Dapr is already installed. Upgrading...${NC}"
    ACTION="upgrade"
else
    echo -e "${YELLOW}Installing Dapr control plane...${NC}"
    ACTION="install"
fi

# Install/Upgrade Dapr
helm ${ACTION} dapr dapr/dapr \
    --namespace ${DAPR_NAMESPACE} \
    --version ${DAPR_VERSION} \
    --set global.ha.enabled=false \
    --set global.logAsJson=true \
    --set dapr_sidecar_injector.sidecarDropALLCapabilities=true \
    --wait \
    --timeout 5m

# Verify installation
echo -e "${YELLOW}Verifying Dapr installation...${NC}"

# Wait for Dapr pods to be ready
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/part-of=dapr \
    -n ${DAPR_NAMESPACE} \
    --timeout=120s

# Display status
echo -e "${GREEN}=== Dapr Installation Complete ===${NC}"
echo ""
echo "Dapr Version: ${DAPR_VERSION}"
echo "Namespace: ${DAPR_NAMESPACE}"
echo ""
echo "Dapr Components:"
kubectl get pods -n ${DAPR_NAMESPACE}
echo ""
echo "To verify Dapr is working:"
echo "  kubectl get pods -n ${DAPR_NAMESPACE}"
echo "  dapr status -k"
echo ""
echo "Next steps:"
echo "  1. Apply Dapr components: kubectl apply -f dapr-components/"
echo "  2. Add Dapr annotations to your deployments"
