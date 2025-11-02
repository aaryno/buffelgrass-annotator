# Remote GPU Training via SDK (SSH-Only Access)

## Overview

This document describes how to perform GPU-accelerated model training on a cloud VM using **only SSH and the Geti SDK**, without requiring web UI access or exposing public ports. This approach simplifies security, reduces complexity, and enables fully scriptable, reproducible training workflows.

## Key Benefits

✅ **No firewall rules required** - No need to expose HTTP/HTTPS ports publicly  
✅ **No external IP needed** - Can use internal-only networking  
✅ **Simpler security model** - Only SSH access required (already secured by GCP)  
✅ **Fully scriptable** - Entire workflow can be automated  
✅ **Reproducible** - Same commands work every time  
✅ **Headless operation** - No browser or GUI required  
✅ **Remote execution** - Can trigger from Mac without interactive SSH session  

## Architecture

```
┌─────────────────────────────────────────┐
│  LOCAL (Mac M2 Max)                     │
│  - Annotate locally in Geti web UI     │
│  - Export project via SDK               │
│  - Upload to GCS                        │
│  - SSH to cloud VM                      │
│  - Execute training script              │
│  - Download trained model from GCS      │
└─────────────────────────────────────────┘
                    │
                    │ SSH only
                    │ (port 22)
                    ▼
┌─────────────────────────────────────────┐
│  CLOUD VM (GCP + GPU)                   │
│  ┌───────────────────────────────────┐  │
│  │  Geti (localhost:8080)            │  │
│  │  - No public web access           │  │
│  │  - Only SDK access via localhost  │  │
│  └───────────────────────────────────┘  │
│                                          │
│  Training script runs via SSH:          │
│  1. Download project from GCS           │
│  2. Import to Geti (SDK)                │
│  3. Start training (SDK)                │
│  4. Monitor progress (SDK)              │
│  5. Export trained model (SDK)          │
│  6. Upload to GCS                       │
└─────────────────────────────────────────┘
                    │
                    │ GCS access
                    ▼
┌─────────────────────────────────────────┐
│  Google Cloud Storage                   │
│  - project_exports/                     │
│  - trained_models/                      │
└─────────────────────────────────────────┘
```

## Prerequisites

- GCP VM with GPU and Geti deployed
- Geti SDK installed on VM: `pip install geti-sdk`
- GCS bucket for project transfers
- `gsutil` configured on both Mac and VM
- Geti API token (generated during initial setup)

## Complete Workflow

### Phase 1: Local Annotation (Mac)

```bash
# Work with local Geti instance
# Web UI at http://localhost:8080
# Annotate 20-30 images using Geti's smart annotation tools
```

### Phase 2: Export Project (Mac)

```python
# scripts/export_local_project.py
from geti_sdk import Geti
from geti_sdk.rest_clients import ProjectClient
from geti_sdk.import_export import GetiIE

# Connect to local Geti
geti = Geti(host="http://localhost:8080", token="local_token")
project_client = ProjectClient(session=geti.session, workspace_id=geti.workspace_id)
geti_ie = GetiIE(workspace_id=geti.workspace_id, 
                 session=geti.session, 
                 project_client=project_client)

# Export annotated project (no models yet)
project = project_client.get_project_by_name("Buffelgrass Segmentation")
geti_ie.export_project(
    project_id=project.id,
    filepath="~/asdm/exports/buffelgrass_batch1.zip",
    include_models="none"
)
print("Project exported successfully")
```

### Phase 3: Upload to GCS (Mac)

```bash
# Upload project export to GCS
gsutil cp ~/asdm/exports/buffelgrass_batch1.zip \
          gs://asdm-buffelgrass/project_exports/

# Verify upload
gsutil ls gs://asdm-buffelgrass/project_exports/
```

### Phase 4: Remote Training (SSH to VM)

#### Option A: Interactive SSH Session

```bash
# SSH into cloud VM
gcloud compute ssh geti-buffelgrass --zone=us-west1-b

# On VM: Download project
gsutil cp gs://asdm-buffelgrass/project_exports/buffelgrass_batch1.zip /tmp/

# On VM: Run training script
python3 /opt/scripts/train_remote.py /tmp/buffelgrass_batch1.zip
```

#### Option B: Non-Interactive Remote Execution

```bash
# Copy script to VM
gcloud compute scp scripts/train_remote.py \
    geti-buffelgrass:/tmp/ --zone=us-west1-b

# Execute remotely and stream output
gcloud compute ssh geti-buffelgrass --zone=us-west1-b \
    --command="python3 /tmp/train_remote.py"

# Entire training runs on VM, logs stream to your Mac terminal
# You can close terminal and training continues
```

### Phase 5: Download Trained Model (Mac)

```bash
# After training completes (you'll see log message)
gsutil cp gs://asdm-buffelgrass/trained_models/buffelgrass_trained_v1.zip \
          ~/asdm/exports/

# Stop VM to save costs
gcloud compute instances stop geti-buffelgrass --zone=us-west1-b
```

## Training Script Template

```python
#!/usr/bin/env python3
"""
Remote GPU training script for Geti
Runs on cloud VM, triggered via SSH
No web UI access required
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from geti_sdk import Geti
from geti_sdk.rest_clients import ProjectClient, TrainingClient
from geti_sdk.import_export import GetiIE

# Configuration
GETI_HOST = "http://localhost:8080"
GETI_TOKEN = os.getenv("GETI_TOKEN", "your_token_here")
GCS_BUCKET = "gs://asdm-buffelgrass"

def download_from_gcs(gcs_path: str, local_path: str):
    """Download file from GCS to local path."""
    print(f"Downloading {gcs_path} to {local_path}...")
    subprocess.run(['gsutil', 'cp', gcs_path, local_path], check=True)
    print("Download complete")

def upload_to_gcs(local_path: str, gcs_path: str):
    """Upload file from local path to GCS."""
    print(f"Uploading {local_path} to {gcs_path}...")
    subprocess.run(['gsutil', 'cp', local_path, gcs_path], check=True)
    print("Upload complete")

def main():
    """Main training workflow."""
    
    # Parse arguments
    project_export_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/project.zip"
    
    print("=" * 60)
    print("GETI REMOTE TRAINING SCRIPT")
    print("=" * 60)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Project export: {project_export_path}")
    print()
    
    # Step 1: Download project from GCS (if not local)
    if not Path(project_export_path).exists():
        gcs_source = f"{GCS_BUCKET}/project_exports/{Path(project_export_path).name}"
        download_from_gcs(gcs_source, project_export_path)
    
    # Step 2: Connect to Geti
    print("\n" + "=" * 60)
    print("CONNECTING TO GETI")
    print("=" * 60)
    geti = Geti(
        host=GETI_HOST,
        token=GETI_TOKEN,
        verify_certificate=False
    )
    print(f"Connected to Geti workspace: {geti.workspace_id}")
    
    # Step 3: Import project
    print("\n" + "=" * 60)
    print("IMPORTING PROJECT")
    print("=" * 60)
    project_client = ProjectClient(
        session=geti.session, 
        workspace_id=geti.workspace_id
    )
    geti_ie = GetiIE(
        workspace_id=geti.workspace_id,
        session=geti.session,
        project_client=project_client
    )
    
    project = geti_ie.import_project(
        filepath=project_export_path,
        project_name="Buffelgrass Segmentation"
    )
    print(f"Project imported: {project.name}")
    print(f"Project ID: {project.id}")
    print(f"Tasks: {[task.title for task in project.get_trainable_tasks()]}")
    
    # Step 4: Setup training client
    print("\n" + "=" * 60)
    print("PREPARING TRAINING")
    print("=" * 60)
    training_client = TrainingClient(
        session=geti.session,
        workspace_id=geti.workspace_id,
        project=project
    )
    
    # Get trainable tasks
    tasks = training_client.get_trainable_tasks()
    if not tasks:
        print("ERROR: No trainable tasks found!")
        sys.exit(1)
    
    task = tasks[0]
    print(f"Training task: {task.title}")
    
    # Get available algorithms
    algorithms = training_client.get_algorithms_for_task(task)
    print(f"Available algorithms: {[algo.name for algo in algorithms.algorithms]}")
    
    # Step 5: Start training
    print("\n" + "=" * 60)
    print("STARTING TRAINING")
    print("=" * 60)
    job = training_client.train_task(task=task)
    print(f"Training job created: {job.id}")
    print(f"Job status: {job.status}")
    print()
    print("Monitoring progress (this will take 30-60 minutes with GPU)...")
    print("You can close this terminal - training will continue on VM")
    print()
    
    # Monitor training (blocks until complete)
    training_client.monitor_job(job)
    
    # Step 6: Export trained model
    print("\n" + "=" * 60)
    print("EXPORTING TRAINED MODEL")
    print("=" * 60)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"buffelgrass_trained_{timestamp}.zip"
    output_path = f"/tmp/{output_filename}"
    
    geti_ie.export_project(
        project_id=project.id,
        filepath=output_path,
        include_models="latest_active"
    )
    print(f"Model exported to: {output_path}")
    
    # Get model info
    from geti_sdk.rest_clients import ModelClient
    model_client = ModelClient(
        session=geti.session,
        workspace_id=geti.workspace_id,
        project=project
    )
    active_models = model_client.get_all_active_models()
    print("\nTrained models:")
    for model in active_models:
        print(f"  - {model.name} (precision: {model.precision})")
    
    # Step 7: Upload to GCS
    print("\n" + "=" * 60)
    print("UPLOADING TO GCS")
    print("=" * 60)
    gcs_destination = f"{GCS_BUCKET}/trained_models/{output_filename}"
    upload_to_gcs(output_path, gcs_destination)
    
    # Summary
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"End time: {datetime.now().isoformat()}")
    print(f"Trained model available at: {gcs_destination}")
    print()
    print("Next steps:")
    print("1. Stop this VM to save costs: gcloud compute instances stop geti-buffelgrass --zone=us-west1-b")
    print("2. Download model to local: gsutil cp {gcs_destination} ~/asdm/exports/")
    print("3. Import to local Geti for next annotation iteration")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        print("Note: Training job may still be running on Geti server")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

## Simplified VM Configuration

Since we don't need public web access, VM setup is much simpler:

```bash
# Create VM without external IP (optional, for max security)
gcloud compute instances create geti-buffelgrass \
    --zone=us-west1-b \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-standard \
    --maintenance-policy=TERMINATE \
    --no-address  # No external IP needed!

# OR create with external IP but no firewall rules
gcloud compute instances create geti-buffelgrass \
    --zone=us-west1-b \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --image-family=ubuntu-2204-lts \
    --boot-disk-size=200GB

# No firewall rules needed! SSH is already enabled by default
# No need to expose ports 80, 443, or 8080
```

## SDK Training Methods

### Basic Training

```python
# Start training with default settings
job = training_client.train_task(task=task)
```

### Advanced Training Options

```python
# Train with specific algorithm
algorithms = training_client.get_algorithms_for_task(task)
rtmdet = [algo for algo in algorithms.algorithms if "rtmdet" in algo.name.lower()][0]

job = training_client.train_task(
    task=task,
    algorithm=rtmdet,
    train_from_scratch=False,  # Continue from checkpoint if available
)
```

### Custom Hyperparameters

```python
from geti_sdk.rest_clients import ConfigurationClient

# Get current configuration
config_client = ConfigurationClient(
    session=geti.session,
    workspace_id=geti.workspace_id,
    project=project
)

config = config_client.get_full_configuration()

# Modify hyperparameters
config.training.batch_size = 8
config.training.num_epochs = 50

# Set new configuration
config_client.set_configuration(config)

# Train with new config
job = training_client.train_task(task=task)
```

### Monitor Training Progress

```python
# Blocking monitor (waits until complete)
training_client.monitor_job(job)

# Non-blocking status check
job_status = training_client.get_job_by_id(job.id)
print(f"Status: {job_status.status}")
print(f"Progress: {job_status.metadata.progress}%")
```

## Error Handling

```python
def train_with_retry(training_client, task, max_retries=3):
    """Train with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            print(f"Training attempt {attempt + 1}/{max_retries}")
            job = training_client.train_task(task=task)
            training_client.monitor_job(job)
            
            # Check if training succeeded
            final_job = training_client.get_job_by_id(job.id)
            if final_job.status == "FINISHED":
                print("Training completed successfully")
                return final_job
            else:
                print(f"Training ended with status: {final_job.status}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    continue
                    
        except Exception as e:
            print(f"Error during training: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                continue
            raise
    
    raise Exception("Training failed after maximum retries")
```

## Troubleshooting

### Check Geti is Running

```bash
# On VM
kubectl get pods -n geti
curl http://localhost:8080/healthz
```

### Check GPU Availability

```bash
# On VM
nvidia-smi
kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}'
```

### View Training Logs

```bash
# On VM
kubectl logs -n geti <training-pod-name> -f
```

### Test SDK Connection

```python
from geti_sdk import Geti

geti = Geti(host="http://localhost:8080", token="your_token")
print(f"Connected! Workspace: {geti.workspace_id}")
```

## Cost Optimization

### VM Lifecycle Management

```bash
# Stop VM when not training (saves ~$0.35/hour)
gcloud compute instances stop geti-buffelgrass --zone=us-west1-b

# Start when ready to train
gcloud compute instances start geti-buffelgrass --zone=us-west1-b

# Check status
gcloud compute instances list --filter="name=geti-buffelgrass"

# Delete when project complete
gcloud compute instances delete geti-buffelgrass --zone=us-west1-b
```

### Automated Shutdown

```bash
# Add to training script to auto-shutdown after training
# (Add to end of train_remote.py)

# Optionally shutdown VM after training
# sudo shutdown -h now
```

## Security Considerations

✅ **No public web UI** - Reduces attack surface  
✅ **SSH-only access** - Leverages GCP's secure SSH infrastructure  
✅ **No firewall rules** - Fewer configuration points  
✅ **Internal networking** - Can use no-external-IP for max security  
✅ **GCS for data transfer** - Authenticated and encrypted  
✅ **Token-based auth** - API tokens can be rotated  

### Best Practices

1. **Store API tokens securely**: Use environment variables or secret management
2. **Limit SSH access**: Use GCP IAM roles to control who can SSH to VM
3. **Rotate tokens**: Regenerate Geti API tokens periodically
4. **Use internal IPs**: Deploy VM without external IP when possible
5. **Enable audit logging**: Track all SSH sessions and API calls

## Performance Notes

- **Training time**: 30-60 minutes with NVIDIA T4 GPU (vs. 5-10 hours on CPU)
- **Model export**: 1-2 minutes for typical segmentation model
- **GCS transfer**: ~30 seconds for 50-100MB project files
- **Total workflow**: ~1-2 hours including transfer time

## Integration with Project Workflow

This SDK approach fits perfectly into the hybrid local/cloud workflow:

1. **Week 1-2**: Annotate locally (Mac) - $0
2. **Week 2**: Export → GCS → Train on cloud (1-2 hours) - $1-2
3. **Week 3**: More annotation locally (Mac) - $0
4. **Week 3**: Export → GCS → Train on cloud (1-2 hours) - $1-2
5. **Repeat 3-5 times**: Total GPU cost $5-10

## Future Enhancements

- **Batch training script**: Train multiple projects in sequence
- **Hyperparameter sweep**: Automated testing of different configurations
- **Scheduled training**: Cron jobs for overnight training
- **Notification system**: Email/Slack alerts when training completes
- **Cost tracking**: Log VM runtime and costs per training session

## References

- [Geti SDK Documentation](https://github.com/open-edge-platform/geti-sdk)
- [Training Client API](https://github.com/open-edge-platform/geti-sdk/blob/main/geti_sdk/rest_clients/training_client.py)
- [Notebook Example: Train Project](https://github.com/open-edge-platform/geti-sdk/blob/main/notebooks/004_train_project.ipynb)
- [GCP SSH Documentation](https://cloud.google.com/compute/docs/instances/connecting-to-instance)

---

**Version:** 1.0  
**Last Updated:** October 29, 2025  
**Author:** ASDM Buffelgrass Mapping Project

