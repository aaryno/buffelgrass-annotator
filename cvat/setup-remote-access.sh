#!/usr/bin/env bash
set -euo pipefail

# Setup CVAT for remote access (team collaboration)
# Allows Windows/Linux collaborators to access your Mac's CVAT instance

echo "🌐 CVAT Remote Access Setup"
echo "============================"
echo ""

# Get local IP address
echo "📍 Finding your Mac's IP address..."
IP_WIFI=$(ipconfig getifaddr en0 2>/dev/null || echo "")
IP_ETH=$(ipconfig getifaddr en1 2>/dev/null || echo "")

if [ -n "$IP_WIFI" ]; then
    LOCAL_IP="$IP_WIFI"
    INTERFACE="WiFi (en0)"
elif [ -n "$IP_ETH" ]; then
    LOCAL_IP="$IP_ETH"
    INTERFACE="Ethernet (en1)"
else
    echo "❌ Could not find network IP address"
    echo "   Make sure you're connected to a network"
    exit 1
fi

echo "✅ Local IP: $LOCAL_IP ($INTERFACE)"
echo ""

# Check if CVAT is running
if ! docker ps | grep -q cvat_server; then
    echo "⚠️  CVAT is not running"
    echo "   Start CVAT first: make cvat-start"
    exit 1
fi

echo "✅ CVAT is running"
echo ""

# Check firewall
echo "🔥 Checking firewall..."
echo "   Note: You may need to allow incoming connections to port 8080"
echo ""

# Test accessibility
echo "🧪 Testing local access..."
if curl -s http://localhost:8080/api/server/about > /dev/null 2>&1; then
    echo "✅ CVAT accessible locally"
else
    echo "❌ CVAT not accessible locally"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Remote Access Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Share this URL with collaborators:"
echo ""
echo "    http://$LOCAL_IP:8080"
echo ""
echo "Credentials (from .cvat.env):"
if [ -f .cvat.env ]; then
    source .cvat.env
    echo "    Username: $CVAT_USERNAME"
    echo "    Password: $CVAT_PASSWORD"
else
    echo "    (Create user manually or run: make cvat-create-user)"
fi
echo ""
echo "Requirements:"
echo "  • Both machines on same WiFi network"
echo "  • Mac firewall allows port 8080"
echo "  • Keep Mac running while collaborating"
echo ""
echo "To test from Windows:"
echo "  1. Open browser"
echo "  2. Go to: http://$LOCAL_IP:8080"
echo "  3. Login with credentials above"
echo ""
echo "Firewall Setup (if needed):"
echo "  System Settings → Network → Firewall"
echo "  → Allow incoming connections for Docker/CVAT"
echo ""

