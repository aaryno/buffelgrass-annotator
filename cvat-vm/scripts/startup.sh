#!/bin/bash
set -e

echo "=== CVAT VM Startup Script ==="
echo "Starting at: $(date)"

# Mount the persistent data disk if not already mounted
DATA_DISK="/dev/disk/by-id/google-cvat-data"
DATA_DIR="/mnt/cvat-data"

if [ -b "$DATA_DISK" ]; then
    echo "Found data disk: $DATA_DISK"
    
    # Create mount point
    mkdir -p "$DATA_DIR"
    
    # Check if disk has a filesystem
    if ! blkid "$DATA_DISK"; then
        echo "Formatting data disk..."
        mkfs.ext4 -F "$DATA_DISK"
    fi
    
    # Mount if not already mounted
    if ! mountpoint -q "$DATA_DIR"; then
        echo "Mounting data disk to $DATA_DIR..."
        mount "$DATA_DISK" "$DATA_DIR"
        
        # Add to fstab for automatic mounting
        if ! grep -q "$DATA_DIR" /etc/fstab; then
            echo "$DATA_DISK $DATA_DIR ext4 defaults,nofail 0 2" >> /etc/fstab
        fi
    else
        echo "Data disk already mounted"
    fi
else
    echo "WARNING: Data disk not found!"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install gcloud CLI if not present (for GCS sync)
if ! command -v gsutil &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    apt-get update
    apt-get install -y google-cloud-cli
fi

# Create CVAT directory structure on persistent disk
CVAT_DIR="$DATA_DIR/cvat"
mkdir -p "$CVAT_DIR"
cd "$CVAT_DIR"

# Download CVAT docker-compose if not present
if [ ! -f "docker-compose.yml" ]; then
    echo "Downloading CVAT docker-compose configuration..."
    curl -fsSL https://raw.githubusercontent.com/cvat-ai/cvat/develop/docker-compose.yml -o docker-compose.yml
    
    # Create .env file
    cat > .env <<EOF
# CVAT Configuration
CVAT_HOST=localhost
CVAT_VERSION=v2.20.0

# PostgreSQL
POSTGRES_USER=cvat
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=cvat

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# Django
DJANGO_SECRET_KEY=$(openssl rand -base64 50)

# Data directories
CVAT_POSTGRES_DATA=$CVAT_DIR/postgres_data
CVAT_REDIS_DATA=$CVAT_DIR/redis_data
CVAT_DATA=$CVAT_DIR/data
CVAT_KEYS=$CVAT_DIR/keys
CVAT_LOGS=$CVAT_DIR/logs
EOF
    
    echo "CVAT configuration created"
fi

# Create data directories
mkdir -p "$CVAT_DIR/postgres_data"
mkdir -p "$CVAT_DIR/redis_data"
mkdir -p "$CVAT_DIR/data"
mkdir -p "$CVAT_DIR/keys"
mkdir -p "$CVAT_DIR/logs"
mkdir -p "$CVAT_DIR/backups"

# Pull latest CVAT images
echo "Pulling CVAT Docker images..."
docker-compose pull

# Start CVAT
echo "Starting CVAT services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for CVAT to be ready..."
sleep 30

# Check if services are running
docker-compose ps

# Create backup script
cat > "$CVAT_DIR/backup-to-gcs.sh" <<'BACKUP_SCRIPT'
#!/bin/bash
# Backup CVAT data to GCS

BACKUP_DIR="/mnt/cvat-data/cvat/backups"
GCS_BUCKET=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-bucket)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== CVAT Backup to GCS ==="
echo "Time: $(date)"

# Backup PostgreSQL
echo "Backing up database..."
docker-compose exec -T cvat_db pg_dump -U cvat cvat > "$BACKUP_DIR/cvat_db_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/cvat_db_$TIMESTAMP.sql"

# Sync data directory
echo "Syncing CVAT data..."
gsutil -m rsync -r /mnt/cvat-data/cvat/data "$GCS_BUCKET/cvat_backups/data/"

# Upload database backup
echo "Uploading database backup..."
gsutil cp "$BACKUP_DIR/cvat_db_$TIMESTAMP.sql.gz" "$GCS_BUCKET/cvat_backups/db/"

# Keep only last 7 days of local backups
find "$BACKUP_DIR" -name "cvat_db_*.sql.gz" -mtime +7 -delete

echo "Backup completed successfully!"
BACKUP_SCRIPT

chmod +x "$CVAT_DIR/backup-to-gcs.sh"

# Setup daily backup cron job
CRON_JOB="0 2 * * * $CVAT_DIR/backup-to-gcs.sh >> $CVAT_DIR/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v backup-to-gcs.sh; echo "$CRON_JOB") | crontab -

echo "=== CVAT Startup Complete ==="
echo "CVAT is running at: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google"):8080"
echo "Data directory: $CVAT_DIR"
echo "Logs: docker-compose logs -f"

