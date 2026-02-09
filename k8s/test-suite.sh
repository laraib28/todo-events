#!/bin/bash
# AI-Generated Kubernetes Deployment Test Suite
# Generated: 2026-01-08
# Purpose: Comprehensive validation tests for Todo app Kubernetes deployment

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    ((TESTS_TOTAL++))
}

pass_test() {
    echo -e "${GREEN}  ✅ PASS${NC} $1"
    ((TESTS_PASSED++))
}

fail_test() {
    echo -e "${RED}  ❌ FAIL${NC} $1"
    ((TESTS_FAILED++))
}

warn_test() {
    echo -e "${YELLOW}  ⚠️  WARN${NC} $1"
}

# Configuration
NAMESPACE="todo-app"
FRONTEND_REPLICAS_EXPECTED=2
BACKEND_REPLICAS_EXPECTED=2

echo "=========================================="
echo "  Kubernetes Deployment Test Suite"
echo "=========================================="
echo ""

# Test Suite 1: Cluster Health
echo -e "${BLUE}═══ Test Suite 1: Cluster Health ═══${NC}"
echo ""

log_test "1.1 Verify Minikube cluster is running"
if minikube status | grep -q "Running"; then
    pass_test "Minikube cluster is running"
else
    fail_test "Minikube cluster is not running"
fi

log_test "1.2 Verify kubectl connectivity"
if kubectl cluster-info &> /dev/null; then
    pass_test "kubectl can connect to cluster"
else
    fail_test "kubectl cannot connect to cluster"
fi

log_test "1.3 Verify cluster nodes are ready"
NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
if [ "$NODE_STATUS" == "True" ]; then
    pass_test "Cluster node is ready"
else
    fail_test "Cluster node is not ready"
fi

echo ""

# Test Suite 2: Namespace and Resources
echo -e "${BLUE}═══ Test Suite 2: Namespace and Resources ═══${NC}"
echo ""

log_test "2.1 Verify namespace exists"
if kubectl get namespace $NAMESPACE &> /dev/null; then
    pass_test "Namespace '$NAMESPACE' exists"
else
    fail_test "Namespace '$NAMESPACE' does not exist"
fi

log_test "2.2 Verify ConfigMap exists"
if kubectl get configmap todo-config -n $NAMESPACE &> /dev/null; then
    pass_test "ConfigMap 'todo-config' exists"
else
    fail_test "ConfigMap 'todo-config' does not exist"
fi

log_test "2.3 Verify Secret exists"
if kubectl get secret todo-secrets -n $NAMESPACE &> /dev/null; then
    pass_test "Secret 'todo-secrets' exists"
else
    fail_test "Secret 'todo-secrets' does not exist"
fi

log_test "2.4 Verify Secret contains required keys"
SECRET_KEYS=$(kubectl get secret todo-secrets -n $NAMESPACE -o jsonpath='{.data}' | grep -o '"[^"]*"' | tr -d '"' | sort)
REQUIRED_KEYS=("BETTER_AUTH_SECRET" "DATABASE_URL" "OPENAI_API_KEY")
MISSING_KEYS=()
for key in "${REQUIRED_KEYS[@]}"; do
    if echo "$SECRET_KEYS" | grep -q "$key"; then
        pass_test "Secret contains key: $key"
    else
        fail_test "Secret missing key: $key"
        MISSING_KEYS+=("$key")
    fi
    ((TESTS_TOTAL++))
done

echo ""

# Test Suite 3: Deployments
echo -e "${BLUE}═══ Test Suite 3: Deployments ═══${NC}"
echo ""

log_test "3.1 Verify frontend deployment exists"
if kubectl get deployment todo-frontend -n $NAMESPACE &> /dev/null; then
    pass_test "Frontend deployment exists"
else
    fail_test "Frontend deployment does not exist"
fi

log_test "3.2 Verify backend deployment exists"
if kubectl get deployment todo-backend -n $NAMESPACE &> /dev/null; then
    pass_test "Backend deployment exists"
else
    fail_test "Backend deployment does not exist"
fi

log_test "3.3 Verify frontend replicas"
FRONTEND_READY=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
FRONTEND_DESIRED=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.status.replicas}')
if [ "$FRONTEND_READY" == "$FRONTEND_DESIRED" ] && [ "$FRONTEND_READY" -ge "$FRONTEND_REPLICAS_EXPECTED" ]; then
    pass_test "Frontend has $FRONTEND_READY/$FRONTEND_DESIRED replicas ready"
else
    fail_test "Frontend replicas not ready: $FRONTEND_READY/$FRONTEND_DESIRED (expected: $FRONTEND_REPLICAS_EXPECTED)"
fi

log_test "3.4 Verify backend replicas"
BACKEND_READY=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
BACKEND_DESIRED=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.status.replicas}')
if [ "$BACKEND_READY" == "$BACKEND_DESIRED" ] && [ "$BACKEND_READY" -ge "$BACKEND_REPLICAS_EXPECTED" ]; then
    pass_test "Backend has $BACKEND_READY/$BACKEND_DESIRED replicas ready"
else
    fail_test "Backend replicas not ready: $BACKEND_READY/$BACKEND_DESIRED (expected: $BACKEND_REPLICAS_EXPECTED)"
fi

echo ""

# Test Suite 4: Pods
echo -e "${BLUE}═══ Test Suite 4: Pods ═══${NC}"
echo ""

log_test "4.1 Verify all pods are running"
NOT_RUNNING=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
if [ "$NOT_RUNNING" -eq 0 ]; then
    pass_test "All pods are in Running state"
else
    fail_test "$NOT_RUNNING pod(s) not in Running state"
    kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running
fi

log_test "4.2 Verify no pods have restart count > 5"
HIGH_RESTARTS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}' | awk '$2 > 5 {print $1}')
if [ -z "$HIGH_RESTARTS" ]; then
    pass_test "No pods have excessive restarts"
else
    warn_test "Pods with high restart count: $HIGH_RESTARTS"
fi

log_test "4.3 Verify frontend pods are ready"
FRONTEND_PODS_READY=$(kubectl get pods -n $NAMESPACE -l app=todo-frontend -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' | grep -c "True")
if [ "$FRONTEND_PODS_READY" -ge "$FRONTEND_REPLICAS_EXPECTED" ]; then
    pass_test "$FRONTEND_PODS_READY frontend pod(s) ready"
else
    fail_test "Only $FRONTEND_PODS_READY/$FRONTEND_REPLICAS_EXPECTED frontend pods ready"
fi

log_test "4.4 Verify backend pods are ready"
BACKEND_PODS_READY=$(kubectl get pods -n $NAMESPACE -l app=todo-backend -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' | grep -c "True")
if [ "$BACKEND_PODS_READY" -ge "$BACKEND_REPLICAS_EXPECTED" ]; then
    pass_test "$BACKEND_PODS_READY backend pod(s) ready"
else
    fail_test "Only $BACKEND_PODS_READY/$BACKEND_REPLICAS_EXPECTED backend pods ready"
fi

log_test "4.5 Check for CrashLoopBackOff errors"
CRASHLOOP=$(kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].state.waiting.reason}{"\n"}{end}' | grep "CrashLoopBackOff" || true)
if [ -z "$CRASHLOOP" ]; then
    pass_test "No pods in CrashLoopBackOff"
else
    fail_test "Pods in CrashLoopBackOff: $CRASHLOOP"
fi

log_test "4.6 Check for ImagePullBackOff errors"
IMAGEPULL=$(kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].state.waiting.reason}{"\n"}{end}' | grep "ImagePullBackOff" || true)
if [ -z "$IMAGEPULL" ]; then
    pass_test "No pods in ImagePullBackOff"
else
    fail_test "Pods in ImagePullBackOff: $IMAGEPULL"
fi

echo ""

# Test Suite 5: Services
echo -e "${BLUE}═══ Test Suite 5: Services ═══${NC}"
echo ""

log_test "5.1 Verify frontend service exists"
if kubectl get service todo-frontend -n $NAMESPACE &> /dev/null; then
    pass_test "Frontend service exists"
else
    fail_test "Frontend service does not exist"
fi

log_test "5.2 Verify backend service exists"
if kubectl get service todo-backend -n $NAMESPACE &> /dev/null; then
    pass_test "Backend service exists"
else
    fail_test "Backend service does not exist"
fi

log_test "5.3 Verify frontend service has endpoints"
FRONTEND_ENDPOINTS=$(kubectl get endpoints todo-frontend -n $NAMESPACE -o jsonpath='{.subsets[0].addresses}' | grep -c "ip" || echo "0")
if [ "$FRONTEND_ENDPOINTS" -gt 0 ]; then
    pass_test "Frontend service has $FRONTEND_ENDPOINTS endpoint(s)"
else
    fail_test "Frontend service has no endpoints"
fi

log_test "5.4 Verify backend service has endpoints"
BACKEND_ENDPOINTS=$(kubectl get endpoints todo-backend -n $NAMESPACE -o jsonpath='{.subsets[0].addresses}' | grep -c "ip" || echo "0")
if [ "$BACKEND_ENDPOINTS" -gt 0 ]; then
    pass_test "Backend service has $BACKEND_ENDPOINTS endpoint(s)"
else
    fail_test "Backend service has no endpoints"
fi

echo ""

# Test Suite 6: Ingress
echo -e "${BLUE}═══ Test Suite 6: Ingress ═══${NC}"
echo ""

log_test "6.1 Verify ingress exists"
if kubectl get ingress todo-ingress -n $NAMESPACE &> /dev/null; then
    pass_test "Ingress 'todo-ingress' exists"
else
    fail_test "Ingress 'todo-ingress' does not exist"
fi

log_test "6.2 Verify ingress has address"
INGRESS_ADDRESS=$(kubectl get ingress todo-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "$INGRESS_ADDRESS" ]; then
    pass_test "Ingress has address: $INGRESS_ADDRESS"
else
    warn_test "Ingress has no address assigned yet (this may be normal for Minikube)"
fi

log_test "6.3 Verify ingress rules configured"
INGRESS_RULES=$(kubectl get ingress todo-ingress -n $NAMESPACE -o jsonpath='{.spec.rules}' | grep -c "host" || echo "0")
if [ "$INGRESS_RULES" -gt 0 ]; then
    pass_test "Ingress has $INGRESS_RULES rule(s) configured"
else
    fail_test "Ingress has no rules configured"
fi

echo ""

# Test Suite 7: Resource Limits
echo -e "${BLUE}═══ Test Suite 7: Resource Limits ═══${NC}"
echo ""

log_test "7.1 Verify frontend has resource limits"
FRONTEND_LIMITS=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits}')
if [ -n "$FRONTEND_LIMITS" ]; then
    pass_test "Frontend has resource limits configured"
else
    warn_test "Frontend has no resource limits"
fi

log_test "7.2 Verify backend has resource limits"
BACKEND_LIMITS=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.limits}')
if [ -n "$BACKEND_LIMITS" ]; then
    pass_test "Backend has resource limits configured"
else
    warn_test "Backend has no resource limits"
fi

log_test "7.3 Verify frontend has resource requests"
FRONTEND_REQUESTS=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests}')
if [ -n "$FRONTEND_REQUESTS" ]; then
    pass_test "Frontend has resource requests configured"
else
    warn_test "Frontend has no resource requests"
fi

log_test "7.4 Verify backend has resource requests"
BACKEND_REQUESTS=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests}')
if [ -n "$BACKEND_REQUESTS" ]; then
    pass_test "Backend has resource requests configured"
else
    warn_test "Backend has no resource requests"
fi

echo ""

# Test Suite 8: Health Checks
echo -e "${BLUE}═══ Test Suite 8: Health Checks ═══${NC}"
echo ""

log_test "8.1 Verify frontend has liveness probe"
FRONTEND_LIVENESS=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}')
if [ -n "$FRONTEND_LIVENESS" ]; then
    pass_test "Frontend has liveness probe configured"
else
    warn_test "Frontend has no liveness probe"
fi

log_test "8.2 Verify frontend has readiness probe"
FRONTEND_READINESS=$(kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}')
if [ -n "$FRONTEND_READINESS" ]; then
    pass_test "Frontend has readiness probe configured"
else
    warn_test "Frontend has no readiness probe"
fi

log_test "8.3 Verify backend has liveness probe"
BACKEND_LIVENESS=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}')
if [ -n "$BACKEND_LIVENESS" ]; then
    pass_test "Backend has liveness probe configured"
else
    warn_test "Backend has no liveness probe"
fi

log_test "8.4 Verify backend has readiness probe"
BACKEND_READINESS=$(kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}')
if [ -n "$BACKEND_READINESS" ]; then
    pass_test "Backend has readiness probe configured"
else
    warn_test "Backend has no readiness probe"
fi

echo ""

# Test Suite 9: Application Endpoints
echo -e "${BLUE}═══ Test Suite 9: Application Endpoints ═══${NC}"
echo ""

log_test "9.1 Verify /etc/hosts has todo.local"
if grep -q "todo.local" /etc/hosts; then
    pass_test "/etc/hosts contains todo.local"
else
    warn_test "/etc/hosts does not contain todo.local (run: echo \"\$(minikube ip) todo.local api.todo.local\" | sudo tee -a /etc/hosts)"
fi

log_test "9.2 Test frontend HTTP endpoint"
if curl -f -s -o /dev/null -w "%{http_code}" http://todo.local --connect-timeout 5 | grep -q "^[23]"; then
    pass_test "Frontend accessible at http://todo.local"
else
    fail_test "Frontend not accessible at http://todo.local"
fi

log_test "9.3 Test backend health endpoint"
HEALTH_RESPONSE=$(curl -s http://api.todo.local/health --connect-timeout 5 || echo "")
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    pass_test "Backend health check passed"
else
    fail_test "Backend health check failed"
fi

log_test "9.4 Test backend API documentation"
if curl -f -s -o /dev/null -w "%{http_code}" http://api.todo.local/docs --connect-timeout 5 | grep -q "^200"; then
    pass_test "Backend API docs accessible"
else
    fail_test "Backend API docs not accessible"
fi

echo ""

# Test Suite 10: Pod Logs
echo -e "${BLUE}═══ Test Suite 10: Pod Logs ═══${NC}"
echo ""

log_test "10.1 Check frontend logs for errors"
FRONTEND_ERRORS=$(kubectl logs -l app=todo-frontend -n $NAMESPACE --tail=50 | grep -i "error" || echo "")
if [ -z "$FRONTEND_ERRORS" ]; then
    pass_test "No errors in frontend logs"
else
    warn_test "Errors found in frontend logs"
    echo "$FRONTEND_ERRORS" | head -n 5
fi

log_test "10.2 Check backend logs for errors"
BACKEND_ERRORS=$(kubectl logs -l app=todo-backend -n $NAMESPACE --tail=50 | grep -i "error" || echo "")
if [ -z "$BACKEND_ERRORS" ]; then
    pass_test "No errors in backend logs"
else
    warn_test "Errors found in backend logs"
    echo "$BACKEND_ERRORS" | head -n 5
fi

echo ""

# Final Summary
echo "=========================================="
echo "         Test Suite Summary"
echo "=========================================="
echo -e "Total Tests:  ${BLUE}$TESTS_TOTAL${NC}"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo "Deployment is healthy and ready for use!"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Review failed tests above and check:"
    echo "  - kubectl get pods -n $NAMESPACE"
    echo "  - kubectl logs -l app=todo-frontend -n $NAMESPACE"
    echo "  - kubectl logs -l app=todo-backend -n $NAMESPACE"
    echo "  - kubectl describe pods -n $NAMESPACE"
    exit 1
fi
