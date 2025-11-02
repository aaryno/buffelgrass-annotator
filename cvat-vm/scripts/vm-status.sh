#!/bin/bash
# Check CVAT VM status
set -e

ZONE="us-west1-b"
VM_NAME="cvat-annotation-vm"

echo "🔍 CVAT VM Status"
echo ""

# Check if VM exists
if ! gcloud --configuration=asdm compute instances describe "$VM_NAME" --zone="$ZONE" &>/dev/null; then
    echo "❌ VM not found. Deploy with: make cvat-vm-deploy"
    exit 1
fi

# Get VM status
STATUS=$(gcloud --configuration=asdm compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(status)')

IP=$(gcloud --configuration=asdm compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "VM Status: $STATUS"
echo "IP Address: $IP"

if [ "$STATUS" = "RUNNING" ]; then
    echo "CVAT URL: http://$IP:8080"
    echo ""
    echo "📊 VM Details:"
    gcloud --configuration=asdm compute instances describe "$VM_NAME" \
        --zone="$ZONE" \
        --format="table(name,machineType.basename(),status,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
    
    echo ""
    echo "🐳 Docker Services:"
    gcloud --configuration=asdm compute ssh "$VM_NAME" --zone="$ZONE" \
        --command="cd /mnt/cvat-data/cvat && sudo docker-compose ps" || echo "Could not connect to VM"
else
    echo ""
    echo "VM is $STATUS"
    echo "Start with: make cvat-vm-start"
fi

