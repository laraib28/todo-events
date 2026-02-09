#!/bin/bash
# AI-Generated Validation Script
# Generated: 2026-01-08
# Purpose: Validate Kubernetes deployment

set -e

echo "✅ Todo App Deployment Validation"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="todo-app"

# Check namespace
echo -e "\n${YELLOW}1. Checking namespace...${NC}"
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Namespace exists${NC}"
else
    echo -e "${RED}❌ Namespace not found${NC}"
    exit 1
fi

# Check deployments
echo -e "\n${YELLOW}2. Checking deployments...${NC}"
FRONTEND_REPLICAS=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
BACKEND_REPLICAS=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

if [ "$FRONTEND_REPLICAS" -ge "1" ]; then
    echo -e "${GREEN}✅ Frontend: ${FRONTEND_REPLICAS}/2 replicas ready${NC}"
else
    echo -e "${RED}❌ Frontend: No replicas ready${NC}"
fi

if [ "$BACKEND_REPLICAS" -ge "1" ]; then
    echo -e "${GREEN}✅ Backend: ${BACKEND_REPLICAS}/2 replicas ready${NC}"
else
    echo -e "${RED}❌ Backend: No replicas ready${NC}"
fi

# Check services
echo -e "\n${YELLOW}3. Checking services...${NC}"
if kubectl get service todo-frontend -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Frontend service exists${NC}"
else
    echo -e "${RED}❌ Frontend service not found${NC}"
fi

if kubectl get service todo-backend -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Backend service exists${NC}"
else
    echo -e "${RED}❌ Backend service not found${NC}"
fi

# Check ingress
echo -e "\n${YELLOW}4. Checking ingress...${NC}"
if kubectl get ingress todo-ingress -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✅ Ingress exists${NC}"
    kubectl get ingress todo-ingress -n $NAMESPACE
else
    echo -e "${RED}❌ Ingress not found${NC}"
fi

# Check pods
echo -e "\n${YELLOW}5. Checking pod status...${NC}"
kubectl get pods -n $NAMESPACE

# Check pod logs for errors
echo -e "\n${YELLOW}6. Checking recent logs for errors...${NC}"
FRONTEND_POD=$(kubectl get pod -n $NAMESPACE -l app=todo-frontend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
BACKEND_POD=$(kubectl get pod -n $NAMESPACE -l app=todo-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$FRONTEND_POD" ]; then
    echo "Frontend logs (last 10 lines):"
    kubectl logs $FRONTEND_POD -n $NAMESPACE --tail=10 2>&1 | head -10
else
    echo -e "${RED}❌ No frontend pod found${NC}"
fi

if [ -n "$BACKEND_POD" ]; then
    echo ""
    echo "Backend logs (last 10 lines):"
    kubectl logs $BACKEND_POD -n $NAMESPACE --tail=10 2>&1 | head -10
else
    echo -e "${RED}❌ No backend pod found${NC}"
fi

# Test endpoints
echo -e "\n${YELLOW}7. Testing endpoints...${NC}"

# Check if /etc/hosts is configured
MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "")
if [ -n "$MINIKUBE_IP" ]; then
    echo "Minikube IP: ${MINIKUBE_IP}"

    if grep -q "todo.local" /etc/hosts; then
        echo -e "${GREEN}✅ /etc/hosts configured${NC}"

        echo ""
        echo "Testing frontend..."
        if curl -s -o /dev/null -w "%{http_code}" http://todo.local --connect-timeout 5 | grep -q "200\|301\|302"; then
            echo -e "${GREEN}✅ Frontend accessible${NC}"
        else
            echo -e "${YELLOW}⚠️  Frontend might not be ready yet${NC}"
        fi

        echo ""
        echo "Testing backend health..."
        if curl -s http://api.todo.local/health --connect-timeout 5 | grep -q "ok"; then
            echo -e "${GREEN}✅ Backend health check passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Backend health check failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  /etc/hosts not configured${NC}"
        echo "Add this line to /etc/hosts:"
        echo "${MINIKUBE_IP} todo.local api.todo.local"
    fi
else
    echo -e "${RED}❌ Cannot get Minikube IP${NC}"
fi

# Summary
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Validation Complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\nAccess your application:"
echo "  Frontend: http://todo.local"
echo "  Backend API: http://api.todo.local/health"
echo "  API Docs: http://api.todo.local/docs"
