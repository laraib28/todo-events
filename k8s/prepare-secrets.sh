#!/bin/bash
# AI-Generated Secrets Preparation Script
# Generated: 2026-01-08
# Purpose: Guide for encoding secrets for Kubernetes

set -e

echo "🔐 Todo App Secrets Preparation Guide"
echo "======================================"

echo ""
echo "This script will help you encode secrets for Kubernetes deployment."
echo "WARNING: Never commit the resulting secret.yaml with real values!"
echo ""

# Function to encode and display
encode_secret() {
    local name=$1
    local prompt=$2
    local example=$3

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Secret: ${name}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Description: ${prompt}"
    if [ -n "$example" ]; then
        echo "Example: ${example}"
    fi
    echo ""
    read -p "Enter value (hidden): " -s value
    echo ""

    if [ -z "$value" ]; then
        echo "❌ Value cannot be empty"
        return 1
    fi

    encoded=$(echo -n "$value" | base64)
    echo "✅ Base64 encoded value:"
    echo "$encoded"
    echo ""
    echo "Add to k8s/secret.yaml:"
    echo "  ${name}: ${encoded}"
    echo ""
}

echo "Choose an option:"
echo "1. Interactive mode - Encode all secrets"
echo "2. Manual mode - Show commands only"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        echo ""
        echo "Starting interactive secret encoding..."

        encode_secret "DATABASE_URL" \
            "PostgreSQL connection string from Neon" \
            "postgresql://user:pass@host/db?sslmode=require"

        encode_secret "OPENAI_API_KEY" \
            "OpenAI API key for GPT-4o" \
            "sk-proj-xxxxxxxxxxxxxxxx"

        encode_secret "BETTER_AUTH_SECRET" \
            "JWT secret for authentication (leave empty to auto-generate)" \
            ""

        if [ -z "$value" ]; then
            echo "Generating random JWT secret..."
            jwt_secret=$(openssl rand -base64 32)
            encoded=$(echo -n "$jwt_secret" | base64)
            echo "✅ Generated and encoded:"
            echo "$encoded"
            echo ""
            echo "Add to k8s/secret.yaml:"
            echo "  BETTER_AUTH_SECRET: ${encoded}"
        fi

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ All secrets encoded!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Next steps:"
        echo "1. Copy the encoded values above"
        echo "2. Update k8s/secret.yaml (replace <BASE64_ENCODED...> placeholders)"
        echo "3. DO NOT commit the updated secret.yaml"
        echo "4. Run: ./k8s/deploy.sh"
        ;;

    2)
        echo ""
        echo "Manual encoding commands:"
        echo ""
        echo "# DATABASE_URL"
        echo 'echo -n "postgresql://user:pass@host/db?sslmode=require" | base64'
        echo ""
        echo "# OPENAI_API_KEY"
        echo 'echo -n "sk-proj-your-key-here" | base64'
        echo ""
        echo "# BETTER_AUTH_SECRET (generate and encode)"
        echo 'echo -n "$(openssl rand -base64 32)" | base64'
        echo ""
        echo "After encoding, update k8s/secret.yaml with the values."
        ;;

    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Remember:"
echo "  - Never commit real secrets to version control"
echo "  - Use a separate secrets manager for production"
echo "  - Rotate secrets regularly"
