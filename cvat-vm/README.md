# CVAT Cloud VM Deployment

Deploy CVAT annotation tool on a cost-effective GCP VM that can be started/stopped to save money.

## Quick Start

```bash
# One-time deployment
make cvat-vm-deploy

# Daily usage
make cvat-vm-start    # Start when you need to annotate (~2 min boot)
make cvat-vm-stop     # Stop when done to save money
make cvat-vm-status   # Check if running
```

## Cost Estimates

- **Running**: ~$0.10/hour ($73/month if always on)
- **40 hours/month**: ~$13-21/month (typical for 4 annotators)
- **Stopped**: ~$5-10/month (disk storage only)
- **Static IP**: ~$7/month (reserved even when stopped)

## Features

✅ **Persistent Data** - All annotations preserved across restarts  
✅ **Static IP** - Same URL every time  
✅ **Auto-backup** - Daily GCS backups at 2 AM  
✅ **Cost-effective** - Pay only when running  
✅ **Multi-user** - Supports 4+ simultaneous annotators  

## Architecture

- **VM**: n2-standard-2 (2 vCPU, 8 GB RAM)
- **Disk**: 100 GB persistent SSD
- **OS**: Ubuntu 22.04 LTS
- **CVAT**: Latest via Docker Compose
- **Backups**: Daily to `gs://tumamoc-2023/cvat_backups/`

## Directory Structure

```
cvat-vm/
├── terraform/          # Infrastructure as Code
│   ├── main.tf        # VM, disk, firewall, static IP
│   ├── variables.tf   # Configuration options
│   └── terraform.tfvars.example
├── scripts/           # VM management scripts
│   ├── startup.sh     # VM initialization (auto-runs on boot)
│   ├── vm-start.sh    # Start VM
│   ├── vm-stop.sh     # Stop VM (with backup)
│   ├── vm-status.sh   # Check status
│   ├── vm-backup.sh   # Manual backup to GCS
│   └── vm-ssh.sh      # SSH into VM
└── README.md          # This file
```

## Deployment

### Prerequisites

1. **Terraform** installed:
   ```bash
   brew install terraform
   ```

2. **GCP authentication**:
   ```bash
   make google-auth
   ```

3. **Enable required APIs**:
   ```bash
   gcloud --configuration=asdm services enable compute.googleapis.com
   ```

### Deploy VM

```bash
make cvat-vm-deploy
```

This will:
1. Create persistent disk (survives VM deletion)
2. Create static IP address
3. Configure firewall rules
4. Launch VM with auto-startup script
5. Install Docker and CVAT
6. Output the CVAT URL

**First boot takes ~5 minutes** to install Docker and download CVAT images.

### Get CVAT URL

```bash
make cvat-vm-status
```

Output:
```
VM Status: RUNNING
IP Address: 34.82.123.45
CVAT URL: http://34.82.123.45:8080
```

## Usage

### Daily Workflow

1. **Start VM** (takes ~2 min):
   ```bash
   make cvat-vm-start
   ```

2. **Annotate** at `http://YOUR_IP:8080`

3. **Stop VM** when done:
   ```bash
   make cvat-vm-stop
   ```
   - Automatically backs up to GCS
   - Stops billing for VM compute
   - Preserves all data on persistent disk

### Backup & Recovery

**Manual backup**:
```bash
make cvat-vm-backup
```

**Backup location**:
- Database: `gs://tumamoc-2023/cvat_backups/db/`
- Data: `gs://tumamoc-2023/cvat_backups/data/`

**Automatic backups**: Daily at 2 AM (if VM is running)

**Restore from backup** (if needed):
```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat

# Restore database
gsutil cp gs://tumamoc-2023/cvat_backups/db/LATEST.sql.gz .
gunzip LATEST.sql.gz
docker-compose exec -T cvat_db psql -U cvat cvat < LATEST.sql

# Restore data
gsutil -m rsync -r gs://tumamoc-2023/cvat_backups/data/ /mnt/cvat-data/cvat/data/
```

### SSH Access

```bash
make cvat-vm-ssh
```

Useful commands on VM:
```bash
cd /mnt/cvat-data/cvat

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Check disk usage
df -h /mnt/cvat-data

# Manual backup
sudo ./backup-to-gcs.sh
```

## Customization

Edit `cvat-vm/terraform/variables.tf` before deploying:

```hcl
# Larger VM for more users
machine_type = "n2-standard-4"  # 4 vCPU, 16 GB RAM

# More storage
data_disk_size_gb = 200

# Restrict access to your IP
allowed_ips = ["YOUR_IP/32"]

# Different region
region = "us-central1"
zone   = "us-central1-a"
```

Then redeploy:
```bash
cd cvat-vm/terraform
terraform apply
```

## Security

**Firewall**: VM is accessible from any IP by default. Restrict in `variables.tf`:
```hcl
allowed_ips = ["YOUR_IP/32"]  # Only your IP
```

**CVAT Authentication**: Create strong passwords for users:
```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose exec cvat_server python manage.py createsuperuser
```

**HTTPS**: For production, add Let's Encrypt:
```bash
# On VM
sudo apt install certbot
# Configure nginx in docker-compose.yml
```

## Troubleshooting

### CVAT not accessible after start

Wait 2-3 minutes for services to start. Check status:
```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose ps
docker-compose logs
```

### Disk full

Check usage:
```bash
make cvat-vm-ssh
df -h /mnt/cvat-data
```

Clean old backups:
```bash
cd /mnt/cvat-data/cvat/backups
rm -f cvat_db_*.sql.gz  # Old local backups (GCS has copies)
```

Resize disk:
```bash
# Edit cvat-vm/terraform/variables.tf
data_disk_size_gb = 200

# Apply change
cd cvat-vm/terraform
terraform apply

# Resize filesystem on VM
make cvat-vm-ssh
sudo resize2fs /dev/disk/by-id/google-cvat-data
```

### Services won't start

Restart VM:
```bash
make cvat-vm-stop
sleep 10
make cvat-vm-start
```

### Lost static IP

If you deleted the IP, create a new one:
```bash
gcloud --configuration=asdm compute addresses create cvat-vm-ip --region=us-west1
```

## Cleanup

### Stop but keep everything
```bash
make cvat-vm-stop  # Preserves disk and IP
```

### Delete VM but keep disk
```bash
gcloud --configuration=asdm compute instances delete cvat-annotation-vm --zone=us-west1-b
# Disk and IP preserved, recreate VM anytime
```

### Delete everything
```bash
make cvat-vm-destroy  # Interactive confirmation required
```

## Migration to Local

Export annotations and run locally:
```bash
# Export from cloud VM
make cvat-vm-backup

# Download to local
gsutil -m rsync -r gs://tumamoc-2023/cvat_backups/data/ ./data/cvat_export/

# Setup local CVAT
make cvat-install
make cvat-create-user

# Import data (via CVAT UI)
```

## Support

- **CVAT Documentation**: https://docs.cvat.ai/
- **GCP Compute**: https://cloud.google.com/compute/docs
- **Project Issues**: See main README.md

## Cost Optimization Tips

1. **Stop when not in use** - Biggest savings
2. **Use preemptible VMs** - 80% cheaper (but can be interrupted)
3. **Schedule startup** - Auto-start during annotation hours
4. **Delete old backups** - Keep only last 30 days in GCS
5. **Use standard disk** - Slower but 50% cheaper than SSD

For cost monitoring:
```bash
# Check current month's costs
gcloud --configuration=asdm billing accounts list
```

