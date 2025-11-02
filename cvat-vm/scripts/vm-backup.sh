#!/bin/bash
# Backup CVAT annotations to GCS
set -e

ZONE="us-west1-b"
VM_NAME="cvat-annotation-vm"

echo "📦 Backing up CVAT annotations to GCS..."

# Check if VM is running
STATUS=$(gcloud --configuration=asdm compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(status)')

if [ "$STATUS" != "RUNNING" ]; then
    echo "❌ VM is not running (status: $STATUS)"
    echo "   Start with: make cvat-vm-start"
    exit 1
fi

# Run backup script on VM
gcloud --configuration=asdm compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo /mnt/cvat-data/cvat/backup-to-gcs.sh"

echo ""
echo "✅ Backup completed!"
echo "   Location: gs://tumamoc-2023/cvat_backups/"
echo "   View: gsutil ls gs://tumamoc-2023/cvat_backups/"

