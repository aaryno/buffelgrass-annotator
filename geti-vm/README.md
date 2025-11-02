# GETI Cloud VM Deployment

This directory contains configuration and setup scripts for deploying GETI on a cloud VM (GCP) for the buffelgrass mapping project.

## Why Cloud VM?

Running GETI locally requires significant resources (~16GB RAM, long build times). A cloud VM provides:
- **More resources** - Can provision VMs with GPUs for faster training
- **Always available** - Keep the instance running for team access
- **Better performance** - Dedicated compute for annotation and training
- **Cost effective** - Only pay when running, can stop when not in use

## Recommended VM Configuration

**For annotation + CPU training:**
- Machine type: `n2-standard-8` (8 vCPUs, 32GB RAM)
- Disk: 200GB SSD
- OS: Ubuntu 22.04 LTS
- Estimated cost: ~$0.39/hour (~$280/month if always on)

**For GPU-accelerated training:**
- Machine type: `n1-standard-8` (8 vCPUs, 30GB RAM)
- GPU: 1x NVIDIA T4 (16GB)
- Disk: 200GB SSD
- OS: Ubuntu 22.04 LTS with GPU drivers
- Estimated cost: ~$0.65/hour (~$468/month if always on)

## Setup Process

### 1. Create GCP VM

```bash
# CPU-only instance
gcloud compute instances create geti-vm \
    --project=asdm \
    --zone=us-west1-b \
    --machine-type=n2-standard-8 \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server

# GPU instance (for faster training)
gcloud compute instances create geti-vm-gpu \
    --project=asdm \
    --zone=us-west1-b \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --metadata=install-nvidia-driver=True \
    --tags=http-server,https-server
```

### 2. Configure Firewall

```bash
# Allow HTTP/HTTPS access to GETI
gcloud compute firewall-rules create allow-geti \
    --project=asdm \
    --allow=tcp:80,tcp:443 \
    --target-tags=http-server,https-server \
    --source-ranges=0.0.0.0/0
```

### 3. SSH and Install Dependencies

```bash
# SSH to VM
gcloud compute ssh geti-vm --project=asdm --zone=us-west1-b

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install k3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | sh -

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kubectl
sudo apt-get update
sudo apt-get install -y kubectl
```

### 4. Deploy GETI

```bash
# Clone repository
git clone https://github.com/open-edge-platform/geti.git
cd geti

# Build and deploy (takes 30-60 min)
make build-image
make publish-image
make build-umbrella-chart
make publish-umbrella-chart

# Install platform
cd platform/services/installer/platform_*/
./platform_installer install
```

### 5. Access GETI

Get the external IP:
```bash
gcloud compute instances describe geti-vm \
    --project=asdm \
    --zone=us-west1-b \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Access GETI at: `http://<EXTERNAL-IP>`

## Cost Management

**Stop VM when not in use:**
```bash
gcloud compute instances stop geti-vm --project=asdm --zone=us-west1-b
```

**Start VM when needed:**
```bash
gcloud compute instances start geti-vm --project=asdm --zone=us-west1-b
```

**Delete VM when done:**
```bash
gcloud compute instances delete geti-vm --project=asdm --zone=us-west1-b
```

## Access from Local Machine

### SSH Port Forwarding
```bash
gcloud compute ssh geti-vm \
    --project=asdm \
    --zone=us-west1-b \
    --ssh-flag="-L 8080:localhost:80"
```

Then access at: `http://localhost:8080`

### Use GETI SDK Remotely

```python
from geti_sdk import Geti

# Connect to remote GETI instance
geti = Geti(
    host="http://<EXTERNAL-IP>",
    username="your-username",
    password="your-password"
)

# Work with projects remotely
project = geti.get_project("buffelgrass-detection")
```

## Data Access

The VM should have access to GCS bucket:
```bash
# Authenticate with service account
gcloud auth activate-service-account --key-file=/path/to/key.json

# Access data
gsutil ls gs://tumamoc-2023/
gsutil cp gs://tumamoc-2023/training_chips/*.tif ./data/
```

## Next Steps

1. Set up automated snapshots for backup
2. Configure monitoring and alerting
3. Set up automatic shutdown during off-hours
4. Configure SSL/TLS for HTTPS access

---

*This VM deployment provides a production-ready GETI environment for the buffelgrass mapping project.*



