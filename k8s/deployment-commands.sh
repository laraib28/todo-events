#!/bin/bash
# AI-Generated Deployment Commands
# Generated: 2026-01-08
# Purpose: Sequential deployment commands for AI-first deployment

# This file contains the exact sequence of commands that would be executed
# for a successful deployment of the Todo app to Minikube

set -e

echo "=========================================="
echo "AI-First Kubernetes Deployment Sequence"
echo "=========================================="

# Phase 1: Verify Prerequisites
echo -e "\n[Phase 1] Verifying Prerequisites..."
minikube status
kubectl cluster-info
kubectl get nodes

# Phase 2: Build Docker Images
echo -e "\n[Phase 2] Building Docker Images..."
echo "Building frontend image..."
docker build -t todo-frontend:latest ./frontend

echo "Building backend image..."
docker build -t todo-backend:latest ./backend

echo "Verifying images..."
docker images | grep todo

# Phase 3: Load Images to Minikube
echo -e "\n[Phase 3] Loading Images to Minikube..."
echo "Loading frontend..."
minikube image load todo-frontend:latest

echo "Loading backend..."
minikube image load todo-backend:latest

echo "Verifying images in Minikube..."
minikube image ls | grep todo

# Phase 4: Prepare Secrets (Manual Step Required)
echo -e "\n[Phase 4] Secret Preparation Required..."
echo "⚠️  MANUAL STEP: Encode secrets in k8s/secret.yaml"
echo "Run: ./k8s/prepare-secrets.sh"
echo "OR manually encode:"
echo "  DATABASE_URL: echo -n 'postgresql://...' | base64"
echo "  OPENAI_API_KEY: echo -n 'sk-proj-...' | base64"
echo "  BETTER_AUTH_SECRET: echo -n \"\$(openssl rand -base64 32)\" | base64"
echo ""
read -p "Press Enter when secrets are configured..."

# Phase 5: Deploy to Kubernetes
echo -e "\n[Phase 5] Deploying to Kubernetes..."

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

# Phase 6: Wait for Rollouts
echo -e "\n[Phase 6] Waiting for Rollouts..."
echo "Waiting for frontend..."
kubectl rollout status deployment/todo-frontend -n todo-app --timeout=120s

echo "Waiting for backend..."
kubectl rollout status deployment/todo-backend -n todo-app --timeout=120s

# Phase 7: Verify Deployment
echo -e "\n[Phase 7] Verifying Deployment..."

echo "Checking pods..."
kubectl get pods -n todo-app

echo "Checking services..."
kubectl get services -n todo-app

echo "Checking ingress..."
kubectl get ingress -n todo-app

echo "Checking endpoints..."
kubectl get endpoints -n todo-app

# Phase 8: Configure Local DNS
echo -e "\n[Phase 8] Configuring Local DNS..."
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

if ! grep -q "todo.local" /etc/hosts; then
    echo "Adding to /etc/hosts..."
    echo "$MINIKUBE_IP todo.local api.todo.local" | sudo tee -a /etc/hosts
else
    echo "DNS entries already exist in /etc/hosts"
fi

# Phase 9: Test Application
echo -e "\n[Phase 9] Testing Application..."

echo "Testing frontend..."
curl -I http://todo.local

echo "Testing backend health..."
curl http://api.todo.local/health

echo "Testing backend API docs..."
curl -I http://api.todo.local/docs

# Summary
echo -e "\n=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  Frontend: http://todo.local"
echo "  Backend API: http://api.todo.local/health"
echo "  API Docs: http://api.todo.local/docs"
echo ""
echo "Kubernetes Resources:"
echo "  Namespace: todo-app"
echo "  Deployments: 2 (frontend, backend)"
echo "  Services: 2 (frontend, backend)"
echo "  Ingress: 1 (NGINX)"
echo "  Pods: 4 total (2 frontend + 2 backend)"
