#!/bin/bash
# AI-Generated Kubernetes Deployment Script
# Generated: 2026-01-08
# Purpose: Automated deployment to Minikube cluster

set -e

echo "🚀 Todo App Kubernetes Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}1. Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found${NC}"
    exit 1
fi

if ! command -v minikube &> /dev/null; then
    echo -e "${RED}❌ minikube not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ kubectl and minikube found${NC}"

# Check if Minikube is running
echo -e "\n${YELLOW}2. Checking Minikube status...${NC}"
if ! minikube status &> /dev/null; then
    echo -e "${RED}❌ Minikube is not running${NC}"
    echo "Start Minikube with: minikube start --cpus=4 --memory=8192"
    exit 1
fi

echo -e "${GREEN}✅ Minikube is running${NC}"

# Check if images exist in Minikube
echo -e "\n${YELLOW}3. Checking Docker images in Minikube...${NC}"
if ! minikube image ls | grep -q "todo-frontend:latest"; then
    echo -e "${RED}❌ todo-frontend:latest not found in Minikube${NC}"
    echo "Build and load with: docker build -t todo-frontend:latest ./frontend && minikube image load todo-frontend:latest"
    exit 1
fi

if ! minikube image ls | grep -q "todo-backend:latest"; then
    echo -e "${RED}❌ todo-backend:latest not found in Minikube${NC}"
    echo "Build and load with: docker build -t todo-backend:latest ./backend && minikube image load todo-backend:latest"
    exit 1
fi

echo -e "${GREEN}✅ Both images found in Minikube${NC}"

# Check if secrets are configured
echo -e "\n${YELLOW}4. Checking secret configuration...${NC}"
if grep -q "<BASE64_ENCODED" k8s/secret.yaml; then
    echo -e "${RED}❌ Secrets not configured${NC}"
    echo "Please update k8s/secret.yaml with actual base64-encoded values"
    echo "See k8s/prepare-secrets.sh for guidance"
    exit 1
fi

echo -e "${GREEN}✅ Secrets configured${NC}"

# Apply manifests
echo -e "\n${YELLOW}5. Deploying to Kubernetes...${NC}"

echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml

echo "Creating Secret..."
kubectl apply -f k8s/secret.yaml

echo "Deploying Frontend..."
kubectl apply -f k8s/deployment-frontend.yaml
kubectl apply -f k8s/service-frontend.yaml

echo "Deploying Backend..."
kubectl apply -f k8s/deployment-backend.yaml
kubectl apply -f k8s/service-backend.yaml

echo "Creating Ingress..."
kubectl apply -f k8s/ingress.yaml

echo -e "${GREEN}✅ All manifests applied${NC}"

# Wait for rollout
echo -e "\n${YELLOW}6. Waiting for deployments to complete...${NC}"

kubectl rollout status deployment/todo-frontend -n todo-app --timeout=120s
kubectl rollout status deployment/todo-backend -n todo-app --timeout=120s

echo -e "${GREEN}✅ Deployments ready${NC}"

# Verify pods
echo -e "\n${YELLOW}7. Verifying pods...${NC}"
kubectl get pods -n todo-app

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Add to /etc/hosts:"
echo "   ${MINIKUBE_IP} todo.local api.todo.local"
echo ""
echo "2. Access application:"
echo "   Frontend: http://todo.local"
echo "   Backend API: http://api.todo.local/health"
echo "   API Docs: http://api.todo.local/docs"
