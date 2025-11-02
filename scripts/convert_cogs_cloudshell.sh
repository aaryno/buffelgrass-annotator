#!/bin/bash
set -e

echo "========================================"
echo "JPEG → COG Conversion via Cloud Shell"
echo "========================================"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$PROJECT_ROOT/scripts"

# Check if GCP project is set
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    export GOOGLE_CLOUD_PROJECT="asdm"
fi

echo "✓ GCP Project: $GOOGLE_CLOUD_PROJECT"
echo ""

# Copy conversion script to Cloud Shell
echo "Copying script to Cloud Shell..."
gcloud cloud-shell scp localhost:"$SCRIPT_DIR/convert_to_cogs.py" cloudshell:~/convert_to_cogs.py --quiet
echo "✓ Script copied"
echo ""

# Run conversion in Cloud Shell
echo "Starting conversion in Cloud Shell..."
echo "========================================"
echo ""

gcloud cloud-shell ssh --authorize-session --command="
    set -e
    
    # Add local bin to PATH
    export PATH=\$PATH:\$HOME/.local/bin
    
    echo 'Installing dependencies...'
    pip install rasterio rio-cogeo google-cloud-storage --quiet
    
    echo ''
    echo 'Starting conversion...'
    echo ''
    
    python ~/convert_to_cogs.py \$@
"

echo ""
echo "========================================"
echo "Conversion complete!"
echo "========================================"
echo ""
echo "COGs uploaded to: gs://tumamoc-2023/cogs/"
echo ""
echo "To check results:"
echo "  gsutil ls gs://tumamoc-2023/cogs/"
echo "  gsutil du -sh gs://tumamoc-2023/cogs/"

