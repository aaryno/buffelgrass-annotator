#!/usr/bin/env bash
set -euo pipefail

# GETI Local Development Setup Script
# Sets up k3d cluster with local registry for GETI annotation platform

CLUSTER_NAME="${CLUSTER_NAME:-geti-local}"
REGISTRY_NAME="${REGISTRY_NAME:-registry.localhost}"
REGISTRY_PORT="${REGISTRY_PORT:-5000}"

echo "🚀 Setting up GETI local development environment"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
for cmd in k3d docker helm kubectl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ $cmd is not installed. Please install it first."
        exit 1
    fi
    echo "✅ $cmd found"
done

# Create local Docker registry
echo ""
echo "🐳 Setting up local Docker registry..."
if docker ps -a --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
    echo "Registry already exists, restarting..."
    docker restart "${REGISTRY_NAME}"
else
    docker run -d -p ${REGISTRY_PORT}:5000 \
        --restart=always \
        --name "${REGISTRY_NAME}" \
        registry:2
    echo "✅ Registry created and running on port ${REGISTRY_PORT}"
fi

# Create k3d cluster with registry
echo ""
echo "☸️  Creating k3d cluster..."
if k3d cluster list | grep -q "${CLUSTER_NAME}"; then
    echo "Cluster ${CLUSTER_NAME} already exists"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        k3d cluster delete "${CLUSTER_NAME}"
    else
        echo "Using existing cluster"
        k3d kubeconfig merge "${CLUSTER_NAME}" --kubeconfig-switch-context
        exit 0
    fi
fi

k3d cluster create "${CLUSTER_NAME}" \
    --registry-use "${REGISTRY_NAME}:${REGISTRY_PORT}" \
    --port "8080:80@loadbalancer" \
    --port "8443:443@loadbalancer" \
    --agents 2 \
    --k3s-arg "--disable=traefik@server:0"

echo "✅ Cluster created successfully"

# Wait for cluster to be ready
echo ""
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo ""
echo "✅ GETI development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Build GETI images from the geti/ directory:"
echo "   cd geti && make build-image"
echo ""
echo "2. Push images to local registry:"
echo "   make publish-image"
echo ""
echo "3. Build and publish Helm charts:"
echo "   make build-umbrella-chart && make publish-umbrella-chart"
echo ""
echo "4. Install GETI using the platform installer:"
echo "   cd platform/services/installer/platform_<TAG>/"
echo "   ./platform_installer install"
echo ""
echo "📝 Access GETI UI at: http://localhost:8080"
echo ""



