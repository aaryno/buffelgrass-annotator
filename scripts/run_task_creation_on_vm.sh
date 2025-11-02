#!/bin/bash
set -e

# Configuration
VM_NAME="cvat-annotation-vm"
ZONE="us-west1-b"
GCLOUD_CONFIG="asdm"
GROUP="${1:-ah}"
ASSIGNEE="${2:-aaryno}"

echo "=========================================="
echo "Creating CVAT Task on VM"
echo "=========================================="
echo "Group: $GROUP"
echo "Assignee: $ASSIGNEE"
echo ""

# Check if VM is running
echo "🔍 Checking VM status..."
VM_STATUS=$(gcloud --configuration=$GCLOUD_CONFIG compute instances describe $VM_NAME --zone=$ZONE --format="value(status)")

if [ "$VM_STATUS" != "RUNNING" ]; then
    echo "❌ VM is not running (status: $VM_STATUS)"
    echo "   Start the VM with: make cvat-vm-start"
    exit 1
fi

echo "✅ VM is running"
echo ""

# Copy script to VM
echo "📤 Copying script to VM..."
gcloud --configuration=$GCLOUD_CONFIG compute scp \
    scripts/create_task_on_vm.py \
    $VM_NAME:/tmp/create_task_on_vm.py \
    --zone=$ZONE

echo "✅ Script copied to VM"
echo ""

# Run the script on VM
echo "=========================================="
echo "Running task creation on VM..."
echo "=========================================="
echo ""

gcloud --configuration=$GCLOUD_CONFIG compute ssh $VM_NAME --zone=$ZONE --command "
set -e

# Install cvat-sdk if not already installed
echo '🔧 Checking for cvat-sdk...'
if ! python3 -c 'import cvat_sdk' 2>/dev/null; then
    echo '📦 Installing cvat-sdk v2.20.0...'
    pip3 install --user cvat-sdk==2.20.0
    echo '✅ cvat-sdk installed'
else
    echo '✅ cvat-sdk already installed'
fi
echo ''

# Run the task creation script
echo '🚀 Starting task creation...'
echo ''
python3 /tmp/create_task_on_vm.py --group $GROUP --assignee $ASSIGNEE
"

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Visit http://35.203.139.174:8080/tasks"
echo "2. Verify the task appears and has images"
echo "3. Try opening the annotation interface"
echo ""
echo "If successful, create all remaining tasks with:"
echo "  python3 scripts/create_all_tasks_on_vm.py"


