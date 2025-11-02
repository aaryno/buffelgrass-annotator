#!/bin/bash
# Stop the CVAT VM (saves money while preserving data)
set -e

ZONE="us-west1-b"
VM_NAME="cvat-annotation-vm"

echo "⚠️  Stopping CVAT VM (data will be preserved)..."

# Backup before stopping
echo "📦 Creating backup..."
gcloud --configuration=asdm compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo /mnt/cvat-data/cvat/backup-to-gcs.sh" || echo "Backup script not found (first run?)"

echo "🛑 Stopping VM..."
gcloud --configuration=asdm compute instances stop "$VM_NAME" --zone="$ZONE"

echo ""
echo "✅ VM stopped successfully!"
echo "   💰 Now paying only for disk storage (~$10/month)"
echo "   📁 All annotations and data are preserved"
echo "   🚀 Restart anytime with: make cvat-vm-start"

