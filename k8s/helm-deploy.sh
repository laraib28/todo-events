#!/bin/bash
# AI-Generated Helm Deployment Automation
# Generated: 2026-01-08
# Purpose: Helm-based deployment with summarized results

set -e

# Color codes for summary
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
RELEASE_NAME="todo-app"
NAMESPACE="todo-app"
CHART_PATH="./helm/todo-app"
TIMEOUT="5m"

# Summary counters
STEPS_TOTAL=0
STEPS_SUCCESS=0
STEPS_FAILED=0
WARNINGS=0

# Helper functions
log_step() {
    echo -e "${BLUE}▶${NC} $1"
    ((STEPS_TOTAL++))
}

success_step() {
    echo -e "${GREEN}✓${NC} $1"
    ((STEPS_SUCCESS++))
}

fail_step() {
    echo -e "${RED}✗${NC} $1"
    ((STEPS_FAILED++))
}

warn_step() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Header
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         AI-First Helm Deployment Automation                ║"
echo "║         Todo App → Minikube                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Phase 1: Pre-Deployment Checks
echo -e "${CYAN}═══ Phase 1: Pre-Deployment Validation ═══${NC}"
echo ""

log_step "Validating Helm installation"
if helm version --short &> /dev/null; then
    HELM_VERSION=$(helm version --short | cut -d' ' -f1)
    success_step "Helm available: $HELM_VERSION"
else
    fail_step "Helm not found"
    exit 1
fi

log_step "Validating kubectl connectivity"
if kubectl cluster-info &> /dev/null; then
    CLUSTER_INFO=$(kubectl config current-context)
    success_step "Connected to cluster: $CLUSTER_INFO"
else
    fail_step "Cannot connect to Kubernetes cluster"
    exit 1
fi

log_step "Validating Minikube status"
if minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    success_step "Minikube running at: $MINIKUBE_IP"
else
    warn_step "Minikube status check failed (may be normal)"
fi

log_step "Checking Docker images"
FRONTEND_IMAGE=$(docker images todo-frontend:latest -q)
BACKEND_IMAGE=$(docker images todo-backend:latest -q)
if [ -n "$FRONTEND_IMAGE" ] && [ -n "$BACKEND_IMAGE" ]; then
    success_step "Docker images present"
else
    fail_step "Missing Docker images - run: docker build -t todo-frontend:latest ./frontend && docker build -t todo-backend:latest ./backend"
    exit 1
fi

log_step "Validating Helm chart"
if helm lint $CHART_PATH &> /dev/null; then
    success_step "Helm chart validation passed"
else
    fail_step "Helm chart validation failed"
    exit 1
fi

echo ""

# Phase 2: Image Loading
echo -e "${CYAN}═══ Phase 2: Image Loading to Minikube ═══${NC}"
echo ""

log_step "Loading frontend image to Minikube"
if minikube image load todo-frontend:latest 2>&1 | grep -q "error"; then
    warn_step "Frontend image load encountered issues"
else
    success_step "Frontend image loaded"
fi

log_step "Loading backend image to Minikube"
if minikube image load todo-backend:latest 2>&1 | grep -q "error"; then
    warn_step "Backend image load encountered issues"
else
    success_step "Backend image loaded"
fi

log_step "Verifying images in Minikube"
IMAGES_COUNT=$(minikube image ls | grep -c "todo-" || echo "0")
if [ "$IMAGES_COUNT" -ge 2 ]; then
    success_step "Images verified in Minikube ($IMAGES_COUNT found)"
else
    warn_step "Image verification incomplete"
fi

echo ""

# Phase 3: Helm Deployment
echo -e "${CYAN}═══ Phase 3: Helm Deployment ═══${NC}"
echo ""

log_step "Checking for existing release"
if helm list -n $NAMESPACE 2>/dev/null | grep -q "$RELEASE_NAME"; then
    warn_step "Release '$RELEASE_NAME' already exists - upgrading"
    HELM_ACTION="upgrade"
else
    success_step "New installation"
    HELM_ACTION="install"
fi

log_step "Executing Helm $HELM_ACTION"
if [ "$HELM_ACTION" == "install" ]; then
    if helm install $RELEASE_NAME $CHART_PATH \
        --namespace $NAMESPACE \
        --create-namespace \
        --timeout $TIMEOUT \
        --wait \
        &> /tmp/helm-deploy.log; then
        success_step "Helm install completed"
    else
        fail_step "Helm install failed - check /tmp/helm-deploy.log"
        cat /tmp/helm-deploy.log
        exit 1
    fi
else
    if helm upgrade $RELEASE_NAME $CHART_PATH \
        --namespace $NAMESPACE \
        --timeout $TIMEOUT \
        --wait \
        &> /tmp/helm-deploy.log; then
        success_step "Helm upgrade completed"
    else
        fail_step "Helm upgrade failed - check /tmp/helm-deploy.log"
        cat /tmp/helm-deploy.log
        exit 1
    fi
fi

log_step "Retrieving release status"
RELEASE_STATUS=$(helm status $RELEASE_NAME -n $NAMESPACE -o json 2>/dev/null | jq -r '.info.status' || echo "unknown")
if [ "$RELEASE_STATUS" == "deployed" ]; then
    success_step "Release status: $RELEASE_STATUS"
else
    fail_step "Release status: $RELEASE_STATUS"
fi

echo ""

# Phase 4: Deployment Validation
echo -e "${CYAN}═══ Phase 4: Deployment Validation ═══${NC}"
echo ""

log_step "Waiting for deployments to be ready"
if kubectl wait --for=condition=available --timeout=120s \
    deployment/todo-frontend deployment/todo-backend -n $NAMESPACE &> /dev/null; then
    success_step "All deployments ready"
else
    warn_step "Some deployments may not be ready yet"
fi

log_step "Checking pod status"
PODS_TOTAL=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
PODS_RUNNING=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
if [ "$PODS_RUNNING" -eq "$PODS_TOTAL" ] && [ "$PODS_TOTAL" -gt 0 ]; then
    success_step "All pods running ($PODS_RUNNING/$PODS_TOTAL)"
else
    warn_step "Pods status: $PODS_RUNNING/$PODS_TOTAL running"
fi

log_step "Checking service endpoints"
FRONTEND_ENDPOINTS=$(kubectl get endpoints todo-frontend -n $NAMESPACE -o json 2>/dev/null | jq -r '.subsets[0].addresses | length' || echo "0")
BACKEND_ENDPOINTS=$(kubectl get endpoints todo-backend -n $NAMESPACE -o json 2>/dev/null | jq -r '.subsets[0].addresses | length' || echo "0")
if [ "$FRONTEND_ENDPOINTS" -gt 0 ] && [ "$BACKEND_ENDPOINTS" -gt 0 ]; then
    success_step "Services have endpoints (frontend: $FRONTEND_ENDPOINTS, backend: $BACKEND_ENDPOINTS)"
else
    fail_step "Service endpoints missing"
fi

log_step "Checking ingress status"
INGRESS_ADDRESS=$(kubectl get ingress todo-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$INGRESS_ADDRESS" ]; then
    success_step "Ingress address: $INGRESS_ADDRESS"
else
    warn_step "Ingress address not yet assigned (normal for Minikube)"
fi

echo ""

# Phase 5: Configuration Validation
echo -e "${CYAN}═══ Phase 5: Configuration Validation ═══${NC}"
echo ""

log_step "Checking /etc/hosts configuration"
if grep -q "todo.local" /etc/hosts 2>/dev/null; then
    success_step "/etc/hosts configured for todo.local"
else
    warn_step "Add to /etc/hosts: $MINIKUBE_IP todo.local api.todo.local"
fi

log_step "Testing DNS resolution"
if ping -c 1 -W 1 todo.local &> /dev/null; then
    success_step "DNS resolution working"
else
    warn_step "DNS resolution failed - check /etc/hosts"
fi

echo ""

# Phase 6: Application Health
echo -e "${CYAN}═══ Phase 6: Application Health Checks ═══${NC}"
echo ""

log_step "Testing frontend accessibility"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://todo.local --connect-timeout 5 2>/dev/null || echo "000")
if [[ "$FRONTEND_STATUS" =~ ^[23] ]]; then
    success_step "Frontend accessible (HTTP $FRONTEND_STATUS)"
else
    warn_step "Frontend not accessible (HTTP $FRONTEND_STATUS)"
fi

log_step "Testing backend health endpoint"
BACKEND_HEALTH=$(curl -s http://api.todo.local/health --connect-timeout 5 2>/dev/null || echo "")
if echo "$BACKEND_HEALTH" | grep -q "ok"; then
    success_step "Backend health check passed"
else
    warn_step "Backend health check failed"
fi

log_step "Testing backend API docs"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://api.todo.local/docs --connect-timeout 5 2>/dev/null || echo "000")
if [ "$DOCS_STATUS" == "200" ]; then
    success_step "API documentation accessible"
else
    warn_step "API documentation not accessible (HTTP $DOCS_STATUS)"
fi

echo ""

# Deployment Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Deployment Summary                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}Release Information:${NC}"
echo "  Name:              $RELEASE_NAME"
echo "  Namespace:         $NAMESPACE"
echo "  Status:            $RELEASE_STATUS"
echo "  Chart Version:     $(helm list -n $NAMESPACE -o json | jq -r '.[0].chart' 2>/dev/null || echo 'unknown')"
echo ""
echo -e "${BLUE}Cluster Information:${NC}"
echo "  Context:           $CLUSTER_INFO"
echo "  Minikube IP:       $MINIKUBE_IP"
echo "  Pods Running:      $PODS_RUNNING/$PODS_TOTAL"
echo ""
echo -e "${BLUE}Application Access:${NC}"
echo "  Frontend:          http://todo.local"
echo "  Backend API:       http://api.todo.local/health"
echo "  API Docs:          http://api.todo.local/docs"
echo ""
echo -e "${BLUE}Validation Results:${NC}"
echo "  Steps Completed:   $STEPS_SUCCESS/$STEPS_TOTAL"
echo "  Steps Failed:      $STEPS_FAILED"
echo "  Warnings:          $WARNINGS"
echo ""

# Exit status
if [ $STEPS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Deployment completed with failures${NC}"
    echo ""
    echo "Review failed steps above and run:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl logs -l tier=frontend -n $NAMESPACE"
    echo "  kubectl logs -l tier=backend -n $NAMESPACE"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Deployment completed with warnings${NC}"
    echo ""
    echo "Review warnings above. Application may still be functional."
    exit 0
else
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Access frontend at http://todo.local"
    echo "  2. Test user registration and login"
    echo "  3. Create tasks and test CRUD operations"
    echo "  4. Test AI chat functionality"
    echo ""
    echo "Run validation tests:"
    echo "  ./k8s/test-suite.sh"
    exit 0
fi
