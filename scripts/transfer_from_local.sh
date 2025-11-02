#!/bin/bash
#
# Run Dropbox → GCS transfer via Cloud Shell from your local machine
# No browser needed!
#
# Usage:
#   ./scripts/transfer_from_local.sh
#
# This script will:
# 1. Copy necessary files to Cloud Shell
# 2. Install dependencies in Cloud Shell
# 3. Run the transfer
# 4. Stream progress to your terminal

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Dropbox → GCS Transfer via Cloud Shell"
echo "========================================"
echo ""

# Check for token file
if [ ! -f "$PROJECT_ROOT/.dropbox-token" ]; then
    echo "❌ Error: .dropbox-token file not found"
    echo "Expected: $PROJECT_ROOT/.dropbox-token"
    exit 1
fi

echo "✓ Found Dropbox token"
echo ""

# Check if gcloud is configured for project
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$PROJECT" != "asdm" ]; then
    echo "Setting GCP project to 'asdm'..."
    gcloud config set project asdm
fi

echo "✓ GCP Project: asdm"
echo ""

# Copy files to Cloud Shell
echo "Copying files to Cloud Shell..."
gcloud cloud-shell scp localhost:"$PROJECT_ROOT/.dropbox-token" cloudshell:~/.dropbox-token --quiet
gcloud cloud-shell scp localhost:"$SCRIPT_DIR/dropbox_to_gcs.py" cloudshell:~/dropbox_to_gcs.py --quiet
echo "✓ Files copied"
echo ""

# Run the transfer in Cloud Shell
echo "Starting transfer in Cloud Shell..."
echo "========================================"
echo ""

gcloud cloud-shell ssh --authorize-session --command="
    set -e
    
    echo 'Installing dependencies...'
    pip install requests google-cloud-storage --quiet
    
    echo 'Loading Dropbox token...'
    export DROPBOX_TOKEN=\$(cat ~/.dropbox-token)
    
    echo ''
    echo 'Starting transfer...'
    echo ''
    
    python ~/dropbox_to_gcs.py
"

echo ""
echo "========================================"
echo "Transfer complete!"
echo "========================================"
echo ""
echo "Files uploaded to: gs://tumamoc-2023/raw_jpegs/"
echo ""
echo "To check results:"
echo "  gsutil ls gs://tumamoc-2023/raw_jpegs/"
echo "  gsutil du -sh gs://tumamoc-2023/raw_jpegs/"

