#!/bin/bash
# SSH into CVAT VM
set -e

ZONE="us-west1-b"
VM_NAME="cvat-annotation-vm"

echo "🔐 Connecting to CVAT VM..."
gcloud --configuration=asdm compute ssh "$VM_NAME" --zone="$ZONE"

