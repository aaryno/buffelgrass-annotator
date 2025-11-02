# CVAT VM Deployment Guide

Step-by-step guide to deploy CVAT on a cost-effective GCP VM.

## Prerequisites (5 minutes)

1. **Install Terraform**:
   ```bash
   brew install terraform
   ```

2. **Authenticate with GCP**:
   ```bash
   make google-auth
   ```

3. **Enable Compute API**:
   ```bash
   gcloud --configuration=asdm services enable compute.googleapis.com
   ```

## Deployment (10 minutes)

### Step 1: Deploy Infrastructure

```bash
make cvat-vm-deploy
```

This creates:
- n2-standard-2 VM (2 vCPU, 8 GB RAM)
- 100 GB persistent SSD disk
- Static public IP address
- Firewall rules

**Terraform will show**:
```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

cvat_external_ip = "34.82.123.45"
cvat_url = "http://34.82.123.45:8080"
ssh_command = "gcloud --configuration=asdm compute ssh cvat-annotation-vm --zone=us-west1-b"
```

**Note the IP address!** This is your permanent CVAT URL.

### Step 2: Wait for First Boot (5 minutes)

The VM is installing Docker and CVAT. Monitor progress:

```bash
make cvat-vm-ssh
sudo journalctl -u google-startup-scripts -f
```

Look for: `=== CVAT Startup Complete ===`

Press `Ctrl+C` and type `exit` to leave SSH.

### Step 3: Access CVAT

Open in browser: `http://YOUR_IP:8080`

**First time**: Create admin user account through web UI:
- Username: `admin`
- Email: `admin@localhost`
- Password: (choose a strong password)

## Daily Usage

### Start VM (when you need to annotate)

```bash
make cvat-vm-start
```

Output shows:
```
✅ CVAT VM is starting up!
   IP Address: 34.82.123.45
   CVAT URL: http://34.82.123.45:8080

⏳ CVAT services are starting (may take 2-3 minutes)...
```

Wait 2-3 minutes, then open `http://YOUR_IP:8080`

### Stop VM (when done for the day)

```bash
make cvat-vm-stop
```

This:
- Creates backup to GCS
- Stops VM to save money
- Preserves all data

**Cost when stopped**: ~$10/month (disk + IP only)

### Check Status

```bash
make cvat-vm-status
```

Shows:
- VM status (RUNNING/STOPPED)
- IP address
- CVAT URL
- Docker services status

## Creating Your First Project

1. **Open CVAT**: `http://YOUR_IP:8080`
2. **Log in** with admin credentials
3. **Create Project**:
   - Click "Projects" → "+ Create new project"
   - Name: "Buffelgrass Detection"
   - Labels: Add "Buffelgrass" (polygon)
4. **Create Task**:
   - Click "Tasks" → "+ Create new task"
   - Name: "Tumamoc 2023 Training Set"
   - Select project: "Buffelgrass Detection"
   - Upload images from `data/training_chips/`
5. **Start Annotating**!

## Backup & Recovery

### Manual Backup

```bash
make cvat-vm-backup
```

Backs up to: `gs://tumamoc-2023/cvat_backups/`

### Automatic Backups

Runs daily at 2 AM (if VM is running)

### View Backups

```bash
gsutil ls gs://tumamoc-2023/cvat_backups/db/
gsutil ls gs://tumamoc-2023/cvat_backups/data/
```

## Multi-User Setup

### Add Users

```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose exec cvat_server python manage.py createsuperuser
```

Or use CVAT web UI: Admin → Users → Add User

### Share with Collaborators

1. Give them the CVAT URL: `http://YOUR_IP:8080`
2. Create accounts for each person
3. Assign tasks to specific users

## Troubleshooting

### Can't access CVAT after start

**Wait 2-3 minutes** for services to start.

Check logs:
```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose logs -f
```

### Services not running

Restart:
```bash
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose restart
```

### VM won't start

Check GCP console or run:
```bash
gcloud --configuration=asdm compute instances describe cvat-annotation-vm --zone=us-west1-b
```

### Forgot IP address

```bash
make cvat-vm-status
```

Or:
```bash
cd cvat-vm/terraform
terraform output cvat_external_ip
```

## Cost Optimization

### Current Cost: ~$0.10/hour when running

**Reduce costs**:

1. **Stop when not in use** (biggest savings):
   ```bash
   make cvat-vm-stop  # Do this daily!
   ```

2. **Use smaller VM** (edit `cvat-vm/terraform/variables.tf`):
   ```hcl
   machine_type = "e2-small"  # $0.03/hour
   ```
   Then: `cd cvat-vm/terraform && terraform apply`

3. **Delete static IP** if you don't need same URL:
   ```bash
   gcloud --configuration=asdm compute addresses delete cvat-vm-ip --region=us-west1
   ```
   Saves $7/month but IP changes each restart.

### Monthly Cost Examples

| Usage Pattern | Cost/Month |
|---------------|------------|
| Always on (730 hrs) | ~$73 |
| 40 hrs/month (stop when not in use) | ~$13-21 |
| Stopped (disk only) | ~$5-10 |

## Exporting Annotations

### Export from CVAT UI

1. Open project in CVAT
2. Click "Export annotations"
3. Select "COCO 1.0"
4. Download ZIP file

### Export via Script

```bash
source venv/bin/activate
python cvat/export-project.py
```

Exports to: `cvat/exports/`

### Export to GCS

Already backed up daily to: `gs://tumamoc-2023/cvat_backups/`

Manual sync:
```bash
gsutil -m rsync -r cvat/exports/ gs://tumamoc-2023/training_annotations/
```

## Advanced Configuration

### Restrict Access to Your IP

Edit `cvat-vm/terraform/variables.tf`:
```hcl
allowed_ips = ["YOUR_IP_ADDRESS/32"]
```

Apply:
```bash
cd cvat-vm/terraform
terraform apply
```

### Larger VM (more users)

Edit `cvat-vm/terraform/variables.tf`:
```hcl
machine_type = "n2-standard-4"  # 4 vCPU, 16 GB RAM
```

Apply:
```bash
cd cvat-vm/terraform
terraform apply
```

### More Storage

Edit `cvat-vm/terraform/variables.tf`:
```hcl
data_disk_size_gb = 200
```

Apply:
```bash
cd cvat-vm/terraform
terraform apply

# Resize filesystem
make cvat-vm-ssh
sudo resize2fs /dev/disk/by-id/google-cvat-data
```

## Cleanup

### Temporarily stop (keeps everything)
```bash
make cvat-vm-stop
```

### Delete VM but keep disk
```bash
gcloud --configuration=asdm compute instances delete cvat-annotation-vm --zone=us-west1-b
# Recreate later with: cd cvat-vm/terraform && terraform apply
```

### Delete everything
```bash
make cvat-vm-destroy
# Type 'destroy' to confirm
```

## Next Steps

1. **Extract training chips**:
   ```bash
   make extract-chips-parallel
   ```

2. **Download chips locally**:
   ```bash
   gsutil -m rsync -r gs://tumamoc-2023/training_chips/1024x1024/01/ data/training_chips/
   ```

3. **Upload to CVAT** via web UI or script

4. **Annotate** at `http://YOUR_IP:8080`

5. **Export annotations** when done

6. **Train model** using GETI

7. **Run inference** on full dataset

## Support

- **CVAT Docs**: https://docs.cvat.ai/
- **Project README**: See main repo README.md
- **GCP Support**: https://cloud.google.com/compute/docs

## Quick Reference

```bash
# Deploy (one-time)
make cvat-vm-deploy

# Daily usage
make cvat-vm-start     # Start VM (~2 min)
make cvat-vm-stop      # Stop VM (saves money)
make cvat-vm-status    # Check status
make cvat-vm-backup    # Manual backup
make cvat-vm-ssh       # SSH access

# Troubleshooting
make cvat-vm-ssh
cd /mnt/cvat-data/cvat
docker-compose logs -f
docker-compose restart

# Cleanup
make cvat-vm-destroy   # Delete everything
```

