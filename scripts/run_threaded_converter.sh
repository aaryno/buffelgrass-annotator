#!/bin/bash
# Run multi-threaded COG converter in Cloud Shell

set -e

echo "⚡ Launching threaded COG converter in Cloud Shell..."
echo ""

# Copy script to Cloud Shell
gcloud cloud-shell scp localhost:$(pwd)/scripts/convert_cogs_threaded.py cloudshell:~/convert_cogs_threaded.py

# Run in Cloud Shell with 8 workers
gcloud cloud-shell ssh --authorize-session --command="
    set -e
    
    echo 'Installing dependencies...'
    pip install rasterio rio-cogeo google-cloud-storage --quiet
    export PATH=\$PATH:\$HOME/.local/bin
    
    echo ''
    echo 'Starting conversion (8 parallel workers)...'
    echo ''
    
    python3 ~/convert_cogs_threaded.py
"

echo ""
echo "✓ Threaded conversion complete!"
echo ""
echo "Check results:"
echo "  make status"



