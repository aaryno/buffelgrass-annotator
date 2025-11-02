#!/bin/bash
#
# Run Dropbox to GCS transfer using token from .dropbox-token file
# 
# Usage:
#   ./scripts/run_dropbox_transfer.sh
#
# Or from Cloud Shell:
#   Upload this script and .dropbox-token file
#   ./run_dropbox_transfer.sh

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check for token file
TOKEN_FILE="$PROJECT_ROOT/.dropbox-token"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "❌ Error: .dropbox-token file not found"
    echo ""
    echo "Expected location: $TOKEN_FILE"
    echo ""
    echo "Create this file with your Dropbox API token:"
    echo "  echo 'sl.your_token_here' > .dropbox-token"
    exit 1
fi

# Read token from file
export DROPBOX_TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n\r')

if [ -z "$DROPBOX_TOKEN" ]; then
    echo "❌ Error: .dropbox-token file is empty"
    exit 1
fi

echo "✓ Loaded Dropbox token from $TOKEN_FILE"
echo ""

# Check if we're in Cloud Shell or local
if [ -f "/google/devshell/bashrc.google" ]; then
    echo "Running in Google Cloud Shell"
else
    echo "Running locally (will upload to Cloud Shell recommended)"
fi

echo ""
echo "Installing dependencies..."
pip install requests google-cloud-storage --quiet

echo ""
echo "Starting transfer..."
echo ""

# Run the Python script
python "$SCRIPT_DIR/dropbox_to_gcs.py"

