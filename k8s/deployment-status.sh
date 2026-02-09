#!/bin/bash
# AI-Generated Deployment Status Summarizer
# Generated: 2026-01-08
# Purpose: Generate clean JSON/YAML summary of deployment status

set -e

# Configuration
NAMESPACE="todo-app"
RELEASE_NAME="todo-app"
OUTPUT_FORMAT="${1:-json}"  # json, yaml, or summary

# Generate JSON status
generate_json() {
    cat <<EOF
{
  "deployment": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "release": {
      "name": "$RELEASE_NAME",
      "namespace": "$NAMESPACE",
      "status": "$(helm status $RELEASE_NAME -n $NAMESPACE -o json 2>/dev/null | jq -r '.info.status' || echo 'not-found')",
      "chart": "$(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].chart' || echo 'unknown')",
      "revision": $(helm list -n $NAMESPACE -o json 2>/dev/null | jq -r '.[0].revision' || echo '0')
    },
    "cluster": {
      "context": "$(kubectl config current-context 2>/dev/null || echo 'unknown')",
      "minikube_ip": "$(minikube ip 2>/dev/null || echo 'unavailable')"
    },
    "resources": {
      "namespace_exists": $(kubectl get namespace $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
      "deployments": {
        "frontend": {
          "exists": $(kubectl get deployment todo-frontend -n $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
          "replicas_desired": $(kubectl get deployment todo-frontend -n $NAMESPACE -o json 2>/dev/null | jq -r '.spec.replicas' || echo '0'),
          "replicas_ready": $(kubectl get deployment todo-frontend -n $NAMESPACE -o json 2>/dev/null | jq -r '.status.readyReplicas // 0'),
          "available": $(kubectl get deployment todo-frontend -n $NAMESPACE -o json 2>/dev/null | jq -r '.status.conditions[] | select(.type=="Available") | .status' || echo 'false')
        },
        "backend": {
          "exists": $(kubectl get deployment todo-backend -n $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
          "replicas_desired": $(kubectl get deployment todo-backend -n $NAMESPACE -o json 2>/dev/null | jq -r '.spec.replicas' || echo '0'),
          "replicas_ready": $(kubectl get deployment todo-backend -n $NAMESPACE -o json 2>/dev/null | jq -r '.status.readyReplicas // 0'),
          "available": $(kubectl get deployment todo-backend -n $NAMESPACE -o json 2>/dev/null | jq -r '.status.conditions[] | select(.type=="Available") | .status' || echo 'false')
        }
      },
      "pods": {
        "total": $(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l),
        "running": $(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l),
        "pending": $(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l),
        "failed": $(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l)
      },
      "services": {
        "frontend": {
          "exists": $(kubectl get service todo-frontend -n $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
          "cluster_ip": "$(kubectl get service todo-frontend -n $NAMESPACE -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo 'none')",
          "endpoints": $(kubectl get endpoints todo-frontend -n $NAMESPACE -o json 2>/dev/null | jq -r '.subsets[0].addresses | length' || echo '0')
        },
        "backend": {
          "exists": $(kubectl get service todo-backend -n $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
          "cluster_ip": "$(kubectl get service todo-backend -n $NAMESPACE -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo 'none')",
          "endpoints": $(kubectl get endpoints todo-backend -n $NAMESPACE -o json 2>/dev/null | jq -r '.subsets[0].addresses | length' || echo '0')
        }
      },
      "ingress": {
        "exists": $(kubectl get ingress todo-ingress -n $NAMESPACE &> /dev/null && echo 'true' || echo 'false'),
        "address": "$(kubectl get ingress todo-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'pending')",
        "hosts": $(kubectl get ingress todo-ingress -n $NAMESPACE -o json 2>/dev/null | jq -r '[.spec.rules[].host] | length' || echo '0')
      }
    },
    "health": {
      "frontend": {
        "url": "http://todo.local",
        "status": "$(curl -s -o /dev/null -w '%{http_code}' http://todo.local --connect-timeout 3 2>/dev/null || echo '000')",
        "accessible": $(curl -s -o /dev/null -w '%{http_code}' http://todo.local --connect-timeout 3 2>/dev/null | grep -q '^[23]' && echo 'true' || echo 'false')
      },
      "backend": {
        "url": "http://api.todo.local/health",
        "status": "$(curl -s -o /dev/null -w '%{http_code}' http://api.todo.local/health --connect-timeout 3 2>/dev/null || echo '000')",
        "accessible": $(curl -s http://api.todo.local/health --connect-timeout 3 2>/dev/null | grep -q 'ok' && echo 'true' || echo 'false'),
        "response": $(curl -s http://api.todo.local/health --connect-timeout 3 2>/dev/null | jq -c '.' || echo 'null')
      }
    }
  }
}
EOF
}

# Generate YAML status
generate_yaml() {
    generate_json | yq eval -P - 2>/dev/null || generate_json | python3 -c "import sys, json, yaml; yaml.dump(json.load(sys.stdin), sys.stdout, default_flow_style=False)"
}

# Generate human-readable summary
generate_summary() {
    local json_data=$(generate_json)

    echo "═══════════════════════════════════════════════════════════"
    echo "           Kubernetes Deployment Status Summary"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Timestamp: $(echo "$json_data" | jq -r '.deployment.timestamp')"
    echo ""
    echo "╔═══ Release ═══╗"
    echo "  Name:      $(echo "$json_data" | jq -r '.deployment.release.name')"
    echo "  Namespace: $(echo "$json_data" | jq -r '.deployment.release.namespace')"
    echo "  Status:    $(echo "$json_data" | jq -r '.deployment.release.status')"
    echo "  Chart:     $(echo "$json_data" | jq -r '.deployment.release.chart')"
    echo "  Revision:  $(echo "$json_data" | jq -r '.deployment.release.revision')"
    echo ""
    echo "╔═══ Cluster ═══╗"
    echo "  Context:      $(echo "$json_data" | jq -r '.deployment.cluster.context')"
    echo "  Minikube IP:  $(echo "$json_data" | jq -r '.deployment.cluster.minikube_ip')"
    echo ""
    echo "╔═══ Deployments ═══╗"

    local fe_ready=$(echo "$json_data" | jq -r '.deployment.resources.deployments.frontend.replicas_ready')
    local fe_desired=$(echo "$json_data" | jq -r '.deployment.resources.deployments.frontend.replicas_desired')
    local fe_available=$(echo "$json_data" | jq -r '.deployment.resources.deployments.frontend.available')

    if [ "$fe_available" == "True" ]; then
        echo "  Frontend:  ✓ $fe_ready/$fe_desired replicas ready"
    else
        echo "  Frontend:  ✗ $fe_ready/$fe_desired replicas ready"
    fi

    local be_ready=$(echo "$json_data" | jq -r '.deployment.resources.deployments.backend.replicas_ready')
    local be_desired=$(echo "$json_data" | jq -r '.deployment.resources.deployments.backend.replicas_desired')
    local be_available=$(echo "$json_data" | jq -r '.deployment.resources.deployments.backend.available')

    if [ "$be_available" == "True" ]; then
        echo "  Backend:   ✓ $be_ready/$be_desired replicas ready"
    else
        echo "  Backend:   ✗ $be_ready/$be_desired replicas ready"
    fi
    echo ""
    echo "╔═══ Pods ═══╗"
    echo "  Total:    $(echo "$json_data" | jq -r '.deployment.resources.pods.total')"
    echo "  Running:  $(echo "$json_data" | jq -r '.deployment.resources.pods.running')"
    echo "  Pending:  $(echo "$json_data" | jq -r '.deployment.resources.pods.pending')"
    echo "  Failed:   $(echo "$json_data" | jq -r '.deployment.resources.pods.failed')"
    echo ""
    echo "╔═══ Services ═══╗"

    local fe_endpoints=$(echo "$json_data" | jq -r '.deployment.resources.services.frontend.endpoints')
    if [ "$fe_endpoints" -gt 0 ]; then
        echo "  Frontend:  ✓ $fe_endpoints endpoint(s)"
    else
        echo "  Frontend:  ✗ No endpoints"
    fi

    local be_endpoints=$(echo "$json_data" | jq -r '.deployment.resources.services.backend.endpoints')
    if [ "$be_endpoints" -gt 0 ]; then
        echo "  Backend:   ✓ $be_endpoints endpoint(s)"
    else
        echo "  Backend:   ✗ No endpoints"
    fi
    echo ""
    echo "╔═══ Ingress ═══╗"
    echo "  Address:  $(echo "$json_data" | jq -r '.deployment.resources.ingress.address')"
    echo "  Hosts:    $(echo "$json_data" | jq -r '.deployment.resources.ingress.hosts') configured"
    echo ""
    echo "╔═══ Application Health ═══╗"

    local fe_accessible=$(echo "$json_data" | jq -r '.deployment.health.frontend.accessible')
    local fe_status=$(echo "$json_data" | jq -r '.deployment.health.frontend.status')
    if [ "$fe_accessible" == "true" ]; then
        echo "  Frontend:  ✓ Accessible (HTTP $fe_status)"
    else
        echo "  Frontend:  ✗ Not accessible (HTTP $fe_status)"
    fi

    local be_accessible=$(echo "$json_data" | jq -r '.deployment.health.backend.accessible')
    local be_status=$(echo "$json_data" | jq -r '.deployment.health.backend.status')
    if [ "$be_accessible" == "true" ]; then
        echo "  Backend:   ✓ Accessible (HTTP $be_status)"
    else
        echo "  Backend:   ✗ Not accessible (HTTP $be_status)"
    fi
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Access URLs:"
    echo "  Frontend:     http://todo.local"
    echo "  Backend API:  http://api.todo.local/health"
    echo "  API Docs:     http://api.todo.local/docs"
    echo ""
}

# Main execution
case "$OUTPUT_FORMAT" in
    json)
        generate_json | jq '.'
        ;;
    yaml)
        generate_yaml
        ;;
    summary|*)
        generate_summary
        ;;
esac
