#!/bin/bash
# AI-Generated Validation Summary Report
# Generated: 2026-01-08
# Purpose: Generate concise validation summary with pass/fail metrics

set -e

# Configuration
NAMESPACE="todo-app"
OUTPUT_DIR="./validation-reports"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$OUTPUT_DIR/validation-$TIMESTAMP.json"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Validation categories
declare -A RESULTS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Helper functions
check() {
    local category=$1
    local name=$2
    local command=$3
    local expected=$4

    ((TOTAL_CHECKS++))

    if eval "$command" &> /dev/null; then
        RESULTS["$category.$name"]="PASS"
        ((PASSED_CHECKS++))
        return 0
    else
        RESULTS["$category.$name"]="FAIL"
        ((FAILED_CHECKS++))
        return 1
    fi
}

check_warn() {
    local category=$1
    local name=$2
    local command=$3

    ((TOTAL_CHECKS++))

    if eval "$command" &> /dev/null; then
        RESULTS["$category.$name"]="PASS"
        ((PASSED_CHECKS++))
        return 0
    else
        RESULTS["$category.$name"]="WARN"
        ((WARNING_CHECKS++))
        return 1
    fi
}

# Run validation checks
echo "Running validation checks..."

# Category 1: Cluster
check "cluster" "minikube_running" "minikube status | grep -q Running"
check "cluster" "kubectl_connected" "kubectl cluster-info"
check "cluster" "node_ready" "kubectl get nodes | grep -q Ready"

# Category 2: Namespace
check "namespace" "exists" "kubectl get namespace $NAMESPACE"
check "namespace" "configmap_exists" "kubectl get configmap todo-config -n $NAMESPACE"
check "namespace" "secret_exists" "kubectl get secret todo-secrets -n $NAMESPACE"

# Category 3: Deployments
check "deployments" "frontend_exists" "kubectl get deployment todo-frontend -n $NAMESPACE"
check "deployments" "backend_exists" "kubectl get deployment todo-backend -n $NAMESPACE"
check "deployments" "frontend_available" "kubectl get deployment todo-frontend -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type==\"Available\")].status}' | grep -q True"
check "deployments" "backend_available" "kubectl get deployment todo-backend -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type==\"Available\")].status}' | grep -q True"

# Category 4: Pods
check "pods" "all_running" "[ \$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers | wc -l) -eq 0 ]"
check "pods" "frontend_ready" "[ \$(kubectl get pods -n $NAMESPACE -l app=todo-frontend -o jsonpath='{.items[*].status.conditions[?(@.type==\"Ready\")].status}' | grep -c True) -ge 1 ]"
check "pods" "backend_ready" "[ \$(kubectl get pods -n $NAMESPACE -l app=todo-backend -o jsonpath='{.items[*].status.conditions[?(@.type==\"Ready\")].status}' | grep -c True) -ge 1 ]"

# Category 5: Services
check "services" "frontend_exists" "kubectl get service todo-frontend -n $NAMESPACE"
check "services" "backend_exists" "kubectl get service todo-backend -n $NAMESPACE"
check "services" "frontend_endpoints" "[ \$(kubectl get endpoints todo-frontend -n $NAMESPACE -o jsonpath='{.subsets[0].addresses}' | grep -c ip) -gt 0 ]"
check "services" "backend_endpoints" "[ \$(kubectl get endpoints todo-backend -n $NAMESPACE -o jsonpath='{.subsets[0].addresses}' | grep -c ip) -gt 0 ]"

# Category 6: Ingress
check "ingress" "exists" "kubectl get ingress todo-ingress -n $NAMESPACE"
check_warn "ingress" "address_assigned" "[ -n \"\$(kubectl get ingress todo-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')\" ]"

# Category 7: DNS and Networking
check_warn "networking" "dns_configured" "grep -q 'todo.local' /etc/hosts"
check_warn "networking" "dns_resolves" "ping -c 1 -W 1 todo.local"

# Category 8: Application Health
check_warn "health" "frontend_accessible" "curl -f -s -o /dev/null http://todo.local --connect-timeout 5"
check_warn "health" "backend_health" "curl -s http://api.todo.local/health --connect-timeout 5 | grep -q ok"
check_warn "health" "backend_docs" "curl -f -s -o /dev/null http://api.todo.local/docs --connect-timeout 5"

# Generate JSON report
cat > "$REPORT_FILE" <<EOF
{
  "validation_report": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "namespace": "$NAMESPACE",
    "summary": {
      "total_checks": $TOTAL_CHECKS,
      "passed": $PASSED_CHECKS,
      "failed": $FAILED_CHECKS,
      "warnings": $WARNING_CHECKS,
      "pass_rate": $(awk "BEGIN {printf \"%.2f\", ($PASSED_CHECKS/$TOTAL_CHECKS)*100}")
    },
    "results": {
EOF

# Add results to JSON
first=true
for key in "${!RESULTS[@]}"; do
    category=$(echo "$key" | cut -d. -f1)
    name=$(echo "$key" | cut -d. -f2)
    status="${RESULTS[$key]}"

    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$REPORT_FILE"
    fi

    echo -n "      \"$key\": {\"category\": \"$category\", \"check\": \"$name\", \"status\": \"$status\"}" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" <<EOF

    },
    "deployment_info": {
      "release": "$(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].name // "not-found"')",
      "chart": "$(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].chart // "unknown"')",
      "revision": $(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].revision // 0'),
      "pods_total": $(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l),
      "pods_running": $(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    }
  }
}
EOF

# Generate human-readable summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "           Validation Summary Report"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Timestamp: $(date)"
echo "Namespace: $NAMESPACE"
echo ""
echo "╔═══ Summary ═══╗"
echo "  Total Checks:  $TOTAL_CHECKS"
echo "  Passed:        $PASSED_CHECKS ($(awk "BEGIN {printf \"%.1f\", ($PASSED_CHECKS/$TOTAL_CHECKS)*100}")%)"
echo "  Failed:        $FAILED_CHECKS"
echo "  Warnings:      $WARNING_CHECKS"
echo ""

# Category breakdown
echo "╔═══ Results by Category ═══╗"
for category in cluster namespace deployments pods services ingress networking health; do
    cat_total=$(echo "${!RESULTS[@]}" | tr ' ' '\n' | grep "^$category\." | wc -l)
    cat_passed=$(for k in "${!RESULTS[@]}"; do [[ $k == $category.* ]] && [[ ${RESULTS[$k]} == "PASS" ]] && echo 1; done | wc -l)
    cat_failed=$(for k in "${!RESULTS[@]}"; do [[ $k == $category.* ]] && [[ ${RESULTS[$k]} == "FAIL" ]] && echo 1; done | wc -l)
    cat_warned=$(for k in "${!RESULTS[@]}"; do [[ $k == $category.* ]] && [[ ${RESULTS[$k]} == "WARN" ]] && echo 1; done | wc -l)

    if [ $cat_total -gt 0 ]; then
        status_icon="✓"
        [ $cat_failed -gt 0 ] && status_icon="✗"
        [ $cat_warned -gt 0 ] && [ $cat_failed -eq 0 ] && status_icon="⚠"

        printf "  %-15s %s  %d/%d passed" "$category:" "$status_icon" "$cat_passed" "$cat_total"
        [ $cat_failed -gt 0 ] && printf " (%d failed)" "$cat_failed"
        [ $cat_warned -gt 0 ] && printf " (%d warnings)" "$cat_warned"
        echo ""
    fi
done

echo ""
echo "╔═══ Deployment Status ═══╗"
echo "  Release:       $(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].name // "not-found"')"
echo "  Chart:         $(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].chart // "unknown"')"
echo "  Pods Running:  $(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)/$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Summary message
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo "✅ All validation checks passed!"
    else
        echo "⚠️  Validation passed with $WARNING_CHECKS warning(s)"
        echo "Review warnings above - application may still be functional"
    fi
    echo ""
    echo "Application is ready for use:"
    echo "  Frontend:     http://todo.local"
    echo "  Backend API:  http://api.todo.local/health"
    echo "  API Docs:     http://api.todo.local/docs"
else
    echo "❌ Validation failed with $FAILED_CHECKS error(s)"
    echo ""
    echo "Review failed checks and troubleshoot:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl logs -l tier=frontend -n $NAMESPACE"
    echo "  kubectl logs -l tier=backend -n $NAMESPACE"
    echo "  kubectl describe pods -n $NAMESPACE"
fi

echo ""
echo "Full report saved to: $REPORT_FILE"
echo ""

# Exit with appropriate code
[ $FAILED_CHECKS -eq 0 ] && exit 0 || exit 1
