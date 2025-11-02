#!/usr/bin/env bash
set -euo pipefail

# CVAT Setup Script for Buffelgrass Annotation
# Sets up CVAT locally using Docker Compose

CVAT_DIR="${HOME}/cvat"
CVAT_VERSION="${CVAT_VERSION:-develop}"

echo "🎨 Setting up CVAT for buffelgrass annotation"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
for cmd in docker git; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ $cmd is not installed. Please install it first."
        exit 1
    fi
    echo "✅ $cmd found"
done

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"

# Clone CVAT if not already present
echo ""
echo "📦 Cloning CVAT repository..."
if [ -d "$CVAT_DIR" ]; then
    echo "CVAT directory already exists at $CVAT_DIR"
    read -p "Update to latest version? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$CVAT_DIR"
        git fetch origin
        git checkout "$CVAT_VERSION"
    fi
else
    git clone https://github.com/opencv/cvat "$CVAT_DIR"
    cd "$CVAT_DIR"
    git checkout "$CVAT_VERSION"
fi

cd "$CVAT_DIR"

# Start CVAT
echo ""
echo "🚀 Starting CVAT..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for CVAT to be ready (this may take 2-3 minutes)..."
timeout=180
elapsed=0
while ! curl -s http://localhost:8080/api/server/about > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout waiting for CVAT to start"
        echo "Check logs with: cd $CVAT_DIR && docker compose logs"
        exit 1
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "Still waiting... (${elapsed}s)"
done

echo ""
echo "✅ CVAT is ready!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 CVAT Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Access CVAT at: http://localhost:8080"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8080 in your browser"
echo "2. Create an account (first user becomes admin)"
echo "3. Create a new project:"
echo "   - Name: Buffelgrass Detection"
echo "   - Labels: buffelgrass (for segmentation)"
echo "4. Upload your training chips"
echo "5. Start annotating!"
echo ""
echo "Useful commands:"
echo "  Stop CVAT:    cd $CVAT_DIR && docker compose stop"
echo "  Start CVAT:   cd $CVAT_DIR && docker compose start"
echo "  View logs:    cd $CVAT_DIR && docker compose logs -f"
echo "  Shutdown:     cd $CVAT_DIR && docker compose down"
echo ""

