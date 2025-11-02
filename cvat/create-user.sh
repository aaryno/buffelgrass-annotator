#!/usr/bin/env bash
set -euo pipefail

# Create initial CVAT admin user via Django management command
# This bypasses the web UI registration requirement

CVAT_CONTAINER="${CVAT_CONTAINER:-cvat_server}"
USERNAME="${CVAT_USERNAME:-admin}"
EMAIL="${CVAT_EMAIL:-admin@localhost}"
PASSWORD="${CVAT_PASSWORD:-}"

echo "👤 CVAT User Creation Script"
echo ""

# Check if CVAT is running
if ! docker ps | grep -q "$CVAT_CONTAINER"; then
    echo "❌ CVAT server container is not running"
    echo "Please start CVAT first: cd ~/cvat && docker compose up -d"
    exit 1
fi

echo "✅ CVAT server is running"

# Get credentials
if [ -z "$PASSWORD" ]; then
    echo ""
    read -p "Username [$USERNAME]: " input_username
    USERNAME="${input_username:-$USERNAME}"
    
    read -p "Email [$EMAIL]: " input_email
    EMAIL="${input_email:-$EMAIL}"
    
    read -sp "Password: " PASSWORD
    echo ""
    
    read -sp "Password (confirm): " PASSWORD_CONFIRM
    echo ""
    
    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
        echo "❌ Passwords do not match"
        exit 1
    fi
fi

echo ""
echo "Creating user:"
echo "  Username: $USERNAME"
echo "  Email: $EMAIL"
echo ""

# Create superuser using Django management command
docker exec -it "$CVAT_CONTAINER" python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Check if user already exists
if User.objects.filter(username='$USERNAME').exists():
    print('⚠️  User "$USERNAME" already exists')
else:
    # Create superuser
    user = User.objects.create_superuser(
        username='$USERNAME',
        email='$EMAIL',
        password='$PASSWORD'
    )
    print('✅ Superuser "$USERNAME" created successfully!')
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ User Creation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "You can now use these credentials:"
echo "  Username: $USERNAME"
echo "  Email: $EMAIL"
echo ""
echo "Login at: http://localhost:8080"
echo ""
echo "To create the project automatically:"
echo "  python cvat/auto-setup-project.py \\"
echo "    --username $USERNAME \\"
echo "    --password YOUR_PASSWORD \\"
echo "    --image-dir ~/asdm-training-data"
echo ""



