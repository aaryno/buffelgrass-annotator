#!/bin/bash
# Start the CVAT VM
set -e

ZONE="us-west1-b"
VM_NAME="cvat-annotation-vm"

echo "🚀 Starting CVAT VM..."
gcloud --configuration=asdm compute instances start "$VM_NAME" --zone="$ZONE"

echo "⏳ Waiting for VM to be ready..."
sleep 10

echo "📡 Getting VM IP address..."
IP=$(gcloud --configuration=asdm compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ CVAT VM is starting up!"
echo "   IP Address: $IP"
echo "   CVAT URL: http://$IP:8080"
echo ""
echo "⏳ CVAT services are starting (may take 2-3 minutes)..."
echo "   Monitor startup: gcloud --configuration=asdm compute ssh $VM_NAME --zone=$ZONE --command='sudo journalctl -u google-startup-scripts -f'"
echo ""
echo "💡 Once ready, open: http://$IP:8080"

