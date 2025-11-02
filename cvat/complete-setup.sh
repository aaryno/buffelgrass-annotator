#!/usr/bin/env bash
set -euo pipefail

# Complete end-to-end CVAT setup:
# 1. Install CVAT
# 2. Create admin user
# 3. Create project with labels
# 4. Upload images

echo "🌾 Complete Buffelgrass Annotation Setup"
echo "=========================================="
echo ""

# Parse arguments
IMAGE_DIR=""
USERNAME="admin"
EMAIL="admin@localhost"
PASSWORD=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --image-dir)
            IMAGE_DIR="$2"
            shift 2
            ;;
        --username)
            USERNAME="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--image-dir DIR] [--username USER] [--email EMAIL] [--password PASS]"
            exit 1
            ;;
    esac
done

# Step 1: Install CVAT if not already running
echo "Step 1: Checking CVAT installation..."
if docker ps | grep -q cvat_server; then
    echo "✅ CVAT is already running"
else
    echo "Installing CVAT..."
    ./cvat/setup.sh
fi

echo ""
echo "Waiting for CVAT to be fully ready..."
sleep 10

# Step 2: Create admin user
echo ""
echo "Step 2: Creating admin user..."

if [ -z "$PASSWORD" ]; then
    read -sp "Enter password for $USERNAME: " PASSWORD
    echo ""
fi

export CVAT_USERNAME="$USERNAME"
export CVAT_EMAIL="$EMAIL"
export CVAT_PASSWORD="$PASSWORD"

docker exec cvat_server python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if User.objects.filter(username='$USERNAME').exists():
    print('⚠️  User "$USERNAME" already exists')
else:
    user = User.objects.create_superuser(
        username='$USERNAME',
        email='$EMAIL',
        password='$PASSWORD'
    )
    print('✅ Superuser "$USERNAME" created!')
EOF

# Step 3 & 4: Create project and upload images
echo ""
echo "Step 3-4: Creating project and uploading images..."

if [ -n "$IMAGE_DIR" ]; then
    if [ -d "$IMAGE_DIR" ]; then
        echo "Using image directory: $IMAGE_DIR"
        python cvat/auto-setup-project.py \
            --username "$USERNAME" \
            --password "$PASSWORD" \
            --image-dir "$IMAGE_DIR"
    else
        echo "⚠️  Image directory not found: $IMAGE_DIR"
        echo "Creating project without images..."
        python cvat/auto-setup-project.py \
            --username "$USERNAME" \
            --password "$PASSWORD"
    fi
else
    echo "No image directory specified, creating project only..."
    python cvat/auto-setup-project.py \
        --username "$USERNAME" \
        --password "$PASSWORD"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Complete Setup Finished!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access CVAT at: http://localhost:8080"
echo "Username: $USERNAME"
echo ""
echo "Your buffelgrass detection project is ready! 🌾"
echo ""



