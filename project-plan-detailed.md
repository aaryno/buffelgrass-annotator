# ASDM Buffelgrass Mapping - Project Plan

## Project Overview

Machine learning pipeline for detecting and mapping buffelgrass (*Pennisetum ciliare*) in southern Arizona using aerial imagery from Air Data Solutions and Intel's Geti platform.

## Implementation Phases

### Phase 1: Data Preprocessing

**Objective:** Convert source imagery to cloud-optimized format and store in cloud

**Steps:**
1. Download Tumamoc source JPEG files from Dropbox
   - Source: [Dropbox - Tumamoc Source Images](https://www.dropbox.com/scl/fo/cxb7mkl80f8ux9sfpfoty/AGhAKqDZ0MNjE4V0ZgrlI6M?rlkey=fu5b5hbr6jo6nn7zsknky4w60&e=1&st=blcns2qb&dl=0)

2. Convert JPEG/JP2 to Cloud-Optimized GeoTIFF (COG)
   - Use `rio-cogeo` for conversion
   - Compression: JPEG quality 90 (good balance for aerial imagery)
   - Internal tiling: 512x512 blocks
   - Generate 5 overview levels for multi-resolution access
   - Preserve all geospatial metadata

3. Upload COGs to Google Cloud Storage bucket
   - Bucket: TBD
   - Structure: `gs://bucket-name/source_cogs/tumamoc/`
   - Enable public or authenticated access for windowed reads

**Deliverables:**
- [ ] All source imagery converted to COG format
- [ ] COGs uploaded to GCS bucket
- [ ] Validation: Verify windowed reads work from cloud

**Tools/Scripts:**
- `scripts/convert_to_cog.py`
- `scripts/upload_to_gcs.py`

---

### Phase 2: Training Chip Generation

**Objective:** Generate diverse training image chips from source COGs

**Approach:**
- Random selection of source images
- Random windowed areas within each image
- Window size: Per Geti recommendations for segmentation (likely 1024x1024 or 512x512)

**Steps:**
1. Determine optimal chip size
   - Research Geti documentation for recommended input size
   - Consider: 512x512, 1024x1024, or 2048x2048
   - Balance: model performance vs. annotation effort vs. context window

2. Implement chip extraction
   - Random sampling strategy
   - Filter out low-information chips (water, uniform areas)
   - Extract N chips per source image (e.g., 10-20)
   - Target: 50-100 initial training chips

3. Quality control
   - Visual inspection of random sample
   - Ensure diversity: lighting, terrain types, vegetation density
   - Verify chips contain potential buffelgrass areas

4. Download chips to local storage
   - Local path: `data/training_chips/`
   - Save with metadata (source image ID, window coordinates)
   - Format: GeoTIFF with spatial reference

**Deliverables:**
- [ ] Chip generation script with configurable parameters
- [ ] Initial set of 50-100 training chips downloaded
- [ ] Chip metadata CSV (source, coordinates, extraction date)

**Tools/Scripts:**
- `scripts/generate_training_chips.py`
- `scripts/validate_chip_diversity.py`

---

### Phase 3: Geti Infrastructure Setup (Hybrid: Local + Cloud)

**Objective:** Deploy Geti locally for annotation, prepare cloud VM for GPU training

**Architecture:** Hybrid approach to minimize cloud costs
- **Local (Mac M2 Max + k3d)**: Annotation and project management (no GPU needed)
- **Cloud (GCP VM + GPU)**: Model training only (GPU-accelerated)
- **Workflow**: Annotate locally → Export project → Import to cloud → Train → Export model → Import back to local

**Note:** Apple Silicon Macs (M2 Max) cannot utilize GPU for training, but are perfectly capable of running Geti for annotation tasks.

**Setup:**

#### 3.1 Local Geti Setup (Annotation Environment)

1. **Create local Kubernetes cluster**
   ```bash
   # On Mac: Install k3d if not already installed
   brew install k3d
   
   # Create cluster for Geti
   k3d cluster create geti-local \
       --port 8080:80@loadbalancer \
       --agents 2 \
       --volume ~/geti-data:/data@all
   
   # Verify cluster
   kubectl cluster-info
   ```

2. **Configure persistent storage**
   ```bash
   # Create local data directory
   mkdir -p ~/geti-data
   
   # This will persist: projects, annotations, media
   # Models will be trained in cloud, then imported back
   ```

3. **Deploy Geti (CPU-only mode)**
   ```bash
   # Clone Geti repository
   cd ~/asdm/geti
   
   # Build for local registry
   make build-image
   
   # Import images to k3d
   k3d image import <image-names> -c geti-local
   
   # Deploy with GPU support disabled
   # Follow Geti installation docs for local deployment
   # Set gpu_support: false during installation
   ```

4. **Access local Geti**
   - URL: `http://localhost:8080`
   - Create admin user and get API token
   - Verify you can upload images and create annotations

**Local Environment Deliverables:**
- [ ] k3d cluster running on Mac
- [ ] Geti deployed (CPU-only, for annotation)
- [ ] Persistent volume at `~/geti-data`
- [ ] Web UI accessible at localhost:8080
- [ ] API token for SDK access

---

#### 3.2 GCP VM Creation (Training Environment)

**Approach:** SSH-only access, no public web UI required. Training triggered via Geti SDK over SSH.

1. **Create GPU-enabled VM (simplified - no firewall rules needed!)**
   ```bash
   # Create VM with NVIDIA T4 GPU
   # No external ports exposed except SSH (default)
   gcloud compute instances create geti-buffelgrass \
       --zone=us-west1-b \
       --machine-type=n1-standard-8 \
       --accelerator=type=nvidia-tesla-t4,count=1 \
       --image-family=ubuntu-2204-lts \
       --image-project=ubuntu-os-cloud \
       --boot-disk-size=200GB \
       --boot-disk-type=pd-standard \
       --maintenance-policy=TERMINATE
   
   # Optional: Create without external IP for maximum security
   # (requires Cloud NAT or VPN for GCS access)
   # --no-address
   ```

   **VM Specs:**
   - Machine type: `n1-standard-8` (8 vCPUs, 30GB RAM)
   - GPU: NVIDIA Tesla T4 (16GB VRAM)
   - Boot disk: 200GB (SSD optional for faster I/O)
   - Estimated cost: ~$0.60/hour (~$440/month if running 24/7)
   - **Strategy:** Only run when training (1-2 hours per iteration)
   
   **Security Benefits:**
   - ✅ No firewall rules needed (only SSH, which is default)
   - ✅ No public web UI exposure
   - ✅ Can use internal IP only (optional)
   - ✅ Simpler configuration, smaller attack surface

#### 3.2 VM Setup

1. **SSH into VM**
   ```bash
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b
   ```

2. **Install prerequisites**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install NVIDIA Container Toolkit
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
       sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   
   # Verify GPU access
   sudo docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
   
   # Install k3s with GPU support
   curl -sfL https://get.k3s.io | sh -s - --docker
   sudo chmod 644 /etc/rancher/k3s/k3s.yaml
   export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
   
   # Install Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   
   # Install NVIDIA device plugin for Kubernetes
   kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
   
   # Verify GPU available in k8s
   kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}'
   ```

#### 3.3 Storage Configuration

1. **Create persistent data directory**
   ```bash
   sudo mkdir -p /data/geti
   sudo chown -R $USER:$USER /data/geti
   ```

2. **Mount GCS bucket (optional for large datasets)**
   ```bash
   # Install gcsfuse
   export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
   echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | \
       sudo tee /etc/apt/sources.list.d/gcsfuse.list
   curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
   sudo apt-get update
   sudo apt-get install -y gcsfuse
   
   # Mount bucket
   mkdir -p ~/gcs-data
   gcsfuse your-bucket-name ~/gcs-data
   ```

#### 3.4 Deploy Geti

1. **Clone Geti repository on VM**
   ```bash
   git clone https://github.com/open-edge-platform/geti.git
   cd geti
   ```

2. **Set up local Docker registry**
   ```bash
   docker run -d -p 5000:5000 --restart=always --name registry registry:2
   ```

3. **Build and publish Geti images**
   ```bash
   # This will take 30-60 minutes
   make build-image
   make publish-image REGISTRY=localhost:5000
   
   # Build helm charts
   make build-umbrella-chart
   make publish-umbrella-chart REGISTRY=localhost:5000
   ```

4. **Deploy Geti with GPU support**
   ```bash
   # Copy installer
   sudo cp platform/services/installer/platform_*/platform_installer /opt/geti/
   cd /opt/geti
   
   # Run installation
   sudo ./platform_installer install
   
   # During installation, configure:
   # - GPU support: YES
   # - GPU provider: NVIDIA
   # - Storage path: /data/geti
   # - Domain: <VM_EXTERNAL_IP>.nip.io (or custom domain)
   ```

#### 3.5 Access Configuration

1. **Get VM external IP**
   ```bash
   gcloud compute instances describe geti-buffelgrass \
       --zone=us-west1-b \
       --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
   ```

2. **Access Geti (SSH only - no web UI needed for training)**
   ```bash
   # SSH into VM
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b
   
   # Geti runs on localhost:8080 inside VM
   # All training operations via SDK (no browser required)
   ```

3. **Get API token (one-time setup)**
   - Access Geti web UI via SSH tunnel (initial setup only):
     ```bash
     gcloud compute ssh geti-buffelgrass --zone=us-west1-b \
         --ssh-flag="-L 8080:localhost:8080"
     ```
   - Open browser to `http://localhost:8080`
   - Create admin user and obtain API token
   - Store token securely (will use in training scripts)
   - **Note:** After token obtained, web UI not needed for training

#### 3.6 Verification

1. **Check GPU availability in Geti**
   ```bash
   # On VM
   kubectl get pods -A
   kubectl logs -n geti <training-pod-name> # Check for GPU detection
   ```

2. **Test SDK connectivity from Mac**
   ```python
   from geti_sdk import Geti
   
   # If using SSH tunnel
   geti = Geti(
       host="http://localhost:8080",
       token="your_token",
       verify_certificate=False
   )
   
   # Or direct connection
   geti = Geti(
       host="http://<EXTERNAL_IP>:8080",
       token="your_token",
       verify_certificate=False
   )
   
   print(geti.workspace_id)  # Should print workspace ID
   ```

**Cloud Environment Deliverables:**
- [ ] GCP VM created with NVIDIA T4 GPU
- [ ] k3s cluster running with GPU support
- [ ] Geti deployed with GPU enabled
- [ ] Persistent storage configured at `/data/geti`
- [ ] SSH tunnel or firewall rules for secure access
- [ ] API token generated for SDK access
- [ ] GPU verification successful

---

#### 3.3 Data Transfer Workflow

**Moving projects between local and cloud:**

1. **Export from local Geti (after annotation)**
   ```python
   # On Mac
   from geti_sdk import Geti
   from geti_sdk.import_export import GetiIE
   
   # Connect to local Geti
   local_geti = Geti(host="http://localhost:8080", token="local_token")
   project_client = ProjectClient(session=local_geti.session, 
                                  workspace_id=local_geti.workspace_id)
   geti_ie = GetiIE(workspace_id=local_geti.workspace_id, 
                    session=local_geti.session, 
                    project_client=project_client)
   
   # Export project with annotations (no models yet)
   project = project_client.get_project_by_name("Buffelgrass Segmentation")
   geti_ie.export_project(
       project_id=project.id,
       filepath="~/asdm/exports/buffelgrass_annotated.zip",
       include_models="none"  # No models to export yet
   )
   ```

2. **Upload to GCS for transfer**
   ```bash
   # Upload export to GCS
   gsutil cp ~/asdm/exports/buffelgrass_annotated.zip \
             gs://asdm-buffelgrass/project_exports/
   ```

3. **Download on cloud VM and import**
   ```bash
   # On cloud VM
   gsutil cp gs://asdm-buffelgrass/project_exports/buffelgrass_annotated.zip \
             /tmp/
   ```
   
   ```python
   # On cloud VM (or via SDK from Mac connecting to cloud)
   cloud_geti = Geti(
       host="http://<CLOUD_VM_IP>:8080",
       token="cloud_token"
   )
   project_client = ProjectClient(session=cloud_geti.session,
                                  workspace_id=cloud_geti.workspace_id)
   geti_ie = GetiIE(workspace_id=cloud_geti.workspace_id,
                    session=cloud_geti.session,
                    project_client=project_client)
   
   # Import project to cloud Geti
   imported_project = geti_ie.import_project(
       filepath="/tmp/buffelgrass_annotated.zip",
       project_name="Buffelgrass Segmentation"
   )
   ```

4. **Train on cloud (GPU accelerated via SDK)**
   ```bash
   # SSH into VM
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b
   
   # Run training script (SDK-based, no web UI needed)
   python3 /opt/scripts/train_remote.py
   ```
   
   Or execute remotely without interactive SSH:
   ```bash
   # From Mac: trigger training and stream logs
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b \
       --command="python3 /opt/scripts/train_remote.py"
   ```
   
   Script handles:
   - Download project from GCS
   - Import to Geti (via SDK)
   - Start training (via SDK)
   - Monitor progress (via SDK)
   - Export trained model (via SDK)
   - Upload to GCS
   
   **See detailed documentation:** [`docs/remote-training-via-sdk.md`](docs/remote-training-via-sdk.md)

5. **Export trained model**
   ```python
   # After training completes
   geti_ie.export_project(
       project_id=imported_project.id,
       filepath="/tmp/buffelgrass_trained.zip",
       include_models="latest_active"  # Export trained model
   )
   
   # Upload to GCS
   # gsutil cp /tmp/buffelgrass_trained.zip gs://asdm-buffelgrass/trained_models/
   ```

6. **Import back to local (optional, for continued annotation)**
   ```bash
   # Download on Mac
   gsutil cp gs://asdm-buffelgrass/trained_models/buffelgrass_trained.zip \
             ~/asdm/exports/
   ```
   
   ```python
   # Import to local Geti
   geti_ie.import_project(
       filepath="~/asdm/exports/buffelgrass_trained.zip",
       project_name="Buffelgrass Segmentation - Iteration 2"
   )
   ```

**Configuration Files:**
- `k8s/k3d-local-setup.sh` - Local k3d setup script
- `k8s/gcp-vm-setup.sh` - Cloud VM creation and setup script
- `scripts/export_local_project.py` - Export from local Geti
- `scripts/train_remote.py` - **Complete SDK-based training script** (runs on VM via SSH)
- `docs/remote-training-via-sdk.md` - **Detailed SSH + SDK training workflow**
- `docs/hybrid-workflow.md` - Complete hybrid workflow documentation
- `docs/cost-management.md` - VM start/stop procedures

**Cost Management:**
```bash
# Create VM only when ready to train
gcloud compute instances create geti-buffelgrass [...]

# Train models (keep VM running)
# Estimated: 2-4 hours per training iteration

# Stop VM when training complete
gcloud compute instances stop geti-buffelgrass --zone=us-west1-b

# Delete VM when project complete (stops all charges)
gcloud compute instances delete geti-buffelgrass --zone=us-west1-b
```

**Estimated Costs (us-west1):**
- Running: ~$0.60/hour
- **Annotation phase:** $0 (local only)
- **Training phase:** ~$2-5 per training iteration (3-8 hours)
- **Total project:** $10-20 (vs. $24-36 for always-on cloud)
- Stopped VM (disk only): ~$8/month for 200GB disk
- **Recommended:** Create VM when ready to train, delete after model export

---

### Phase 4: Project Setup & Image Management

**Objective:** Create Geti project and load training chips

**Decision Point: Image Loading Strategy**

Given cloud deployment, we'll use **Option C: Upload via SDK** with GCS integration:

**Chosen Approach: Direct Upload to Local Geti**
- Generate chips on Mac
- Upload directly to local Geti instance via SDK
- Pros: Fast local access, no cloud transfer during annotation phase
- Annotations stored in local persistent volume (`~/geti-data`)

**Workflow:**
```python
# On Mac: Generate chips locally
# scripts/generate_training_chips.py

# Upload directly to local Geti
# scripts/upload_training_data.py
from geti_sdk import Geti
from geti_sdk.rest_clients import ImageClient
from pathlib import Path
import cv2

# Connect to local Geti
geti = Geti(host="http://localhost:8080", token="local_token")
image_client = ImageClient(session=geti.session, 
                          workspace_id=geti.workspace_id, 
                          project=project)

# Upload chips
chips_dir = Path('data/training_chips')
for chip_path in chips_dir.glob('*.tif'):
    image = cv2.imread(str(chip_path))
    image_client.upload_image(image)
    print(f"Uploaded {chip_path.name}")
```

**Steps:**
1. Create Geti project via SDK
   ```python
   from geti_sdk import Geti
   from geti_sdk.rest_clients import ProjectClient
   
   geti = Geti(host="http://localhost:8080", token="your_token")
   project_client = ProjectClient(session=geti.session, workspace_id=geti.workspace_id)
   
   project = project_client.create_project(
       project_name="Buffelgrass Segmentation - Tumamoc",
       project_type="segmentation",
       labels=[["buffelgrass", "background"]]  # Semantic segmentation
   )
   ```

2. Upload training chips via SDK
   ```python
   from geti_sdk.rest_clients import ImageClient
   from pathlib import Path
   
   image_client = ImageClient(session=geti.session, workspace_id=geti.workspace_id, project=project)
   
   chips_dir = Path('data/training_chips')
   for chip_path in chips_dir.glob('*.tif'):
       image = cv2.imread(str(chip_path))
       image_client.upload_image(image)
   ```

3. Verify project configuration
   - Confirm images loaded correctly
   - Check segmentation task configuration
   - Verify data saved to persistent volume

**Deliverables:**
- [ ] Geti project created
- [ ] Training chips uploaded
- [ ] SDK scripts for project management
- [ ] Project configuration documented

**Tools/Scripts:**
- `scripts/create_geti_project.py`
- `scripts/upload_training_data.py`

---

### Phase 5: Annotation (Local) & Model Training (Cloud)

**Objective:** Annotate training data locally, train models on cloud GPU

**Annotation Phase (Local Geti):**

1. **Initial annotation batch (20-30 images)**
   - Use local Geti web UI at `http://localhost:8080`
   - Leverage smart annotation tools:
     - Segment Anything Model (SAM) for assisted segmentation
     - Visual prompting for faster labeling
   - Label buffelgrass vs. background
   - Document annotation guidelines (what counts as buffelgrass?)
   - **Time commitment:** ~30-60 minutes per image with assisted tools
   - **Total:** ~10-30 hours of annotation work

2. **Quality control**
   - Consistent labeling standards
   - Inter-annotator agreement if multiple annotators
   - Edge case documentation

3. **Annotation guidelines**
   - Minimum patch size to label
   - How to handle mixed pixels
   - Dead vs. live buffelgrass (if distinguishable)
   - Seasonal variations

4. **Export annotated project**
   ```python
   # After annotating 20-30 images
   geti_ie.export_project(
       project_id=project.id,
       filepath="~/asdm/exports/buffelgrass_batch1.zip",
       include_models="none"
   )
   ```

**Model Training Phase (Cloud GPU):**

1. **Prepare cloud environment**
   ```bash
   # Start cloud VM (if stopped)
   gcloud compute instances start geti-buffelgrass --zone=us-west1-b
   
   # Wait for boot (~30 seconds)
   # SSH and verify Geti is running
   ```

2. **Transfer and import project**
   ```bash
   # Upload to GCS
   gsutil cp ~/asdm/exports/buffelgrass_batch1.zip \
             gs://asdm-buffelgrass/project_exports/
   
   # Download on VM and import (or use SDK from Mac)
   ```

3. **Initial training on cloud (SDK-based, no web UI required)**
   ```bash
   # SSH and run training script
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b
   python3 /opt/scripts/train_remote.py
   
   # Or trigger remotely from Mac (non-interactive)
   gcloud compute ssh geti-buffelgrass --zone=us-west1-b \
       --command="python3 /opt/scripts/train_remote.py"
   ```
   - All operations via Geti SDK (no browser needed)
   - Uses default model architecture (likely RTMDet or MaskRCNN)
   - Monitor progress via SDK logging
   - Training time: **~30-60 minutes** with GPU (vs. 5-10 hours on CPU)
   - See: [`docs/remote-training-via-sdk.md`](docs/remote-training-via-sdk.md) for complete script

4. **Model evaluation**
   - Review predictions on held-out test set
   - Check confusion areas
   - Visual inspection of segmentation quality
   - Metrics: IoU, pixel accuracy, F1-score

5. **Export trained model**
   ```python
   # After training completes
   geti_ie.export_project(
       project_id=project.id,
       filepath="/tmp/buffelgrass_trained_v1.zip",
       include_models="latest_active"
   )
   
   # Upload to GCS
   gsutil cp /tmp/buffelgrass_trained_v1.zip \
             gs://asdm-buffelgrass/trained_models/
   ```

6. **Stop cloud VM**
   ```bash
   # Save costs when not training
   gcloud compute instances stop geti-buffelgrass --zone=us-west1-b
   ```

7. **Active learning iteration**
   - Import trained model back to local Geti (optional)
   - Use predictions to identify hard cases
   - Annotate suggested images locally
   - Export updated project
   - Re-import to cloud and retrain
   - Repeat 3-5 iterations until satisfied

**Hybrid Workflow Summary:**
```
Annotate locally (10-30 hrs) → Export project → 
Upload to GCS → Import to cloud → 
Train on GPU (0.5-1 hr) → Export model → 
Download from GCS → Stop VM → 
Review results locally → Repeat
```

**Deliverables:**
- [ ] 50-100 annotated training images (local)
- [ ] Annotation guidelines document
- [ ] Trained segmentation model (from cloud)
- [ ] Model performance metrics
- [ ] Exported model artifacts in GCS

**Documentation:**
- `docs/annotation_guidelines.md`
- `docs/model_training_log.md` - Training iterations and results
- `docs/hybrid_workflow_log.md` - Track each export/import cycle

**Cost Savings:**
- Annotation: $0 (local only)
- Training iteration: ~$0.50-1.00 (30-60 minutes)
- Total for 5 iterations: **~$5-10** (vs. $30 for always-on cloud)

---

### Phase 6: Model Inspection & Iteration

**Objective:** Validate model performance and refine as needed

**Activities:**

1. **Visual inspection**
   - Apply model to unannotated chips
   - Review predictions in Geti UI
   - Identify systematic errors or biases

2. **Error analysis**
   - False positives: What's being misclassified as buffelgrass?
   - False negatives: What buffelgrass is being missed?
   - Boundary accuracy: Are edges clean?

3. **Targeted improvement**
   - Annotate more examples of problem areas
   - Balance class distribution if needed
   - Consider additional training data from different seasons/conditions

4. **Model comparison**
   - Try different architectures if available
   - Compare metrics across model versions
   - Select best model for full inference

**Deliverables:**
- [ ] Error analysis report
- [ ] Final model selection and justification
- [ ] Model performance documentation

**Tools:**
- `notebooks/model_evaluation.ipynb`
- Geti web UI for visualization

---

### Phase 7: Full Imagery Inference

**Objective:** Apply trained model to all source COGs in GCS bucket

**Approach:**

1. **Inference infrastructure**
   - Deploy model for inference (local or cloud)
   - Options:
     - Local inference using Geti deployment model
     - Export OpenVINO model and run standalone
     - Cloud-based inference (GCP AI Platform or Vertex AI)

2. **Tile-based inference strategy**
   - Read COGs from GCS using windowed reads
   - Process in tiles matching training chip size
   - Handle tile overlaps for seamless output
   - Stitch predictions back together

3. **Batch processing**
   - Process all Tumamoc COGs
   - Save predictions as COG format (for re-mosaicing)
   - Include confidence scores as additional band

4. **Output format**
   - Prediction rasters: Binary (buffelgrass/background) + confidence
   - Same spatial reference as input COGs
   - COG format for efficient access and mosaicing

5. **Upload to GCS**
   - Store prediction COGs in GCS bucket
   - Structure: `gs://bucket-name/predictions/tumamoc/`
   - Provide access to Stephen for mosaicing

**Deliverables:**
- [ ] Inference pipeline script
- [ ] All source COGs processed
- [ ] Prediction COGs uploaded to GCS
- [ ] Inference performance metrics (time, throughput)

**Tools/Scripts:**
- `scripts/run_inference_on_cogs.py`
- `scripts/stitch_predictions.py`

---

### Phase 8: Mosaic Generation & Delivery

**Objective:** Create final buffelgrass distribution map

**Workflow:**

1. **Coordinate with Stephen (Air Data Solutions)**
   - Provide GCS bucket access to prediction COGs
   - Share mosaic configuration details
   - Confirm output format requirements

2. **Re-mosaicing by ADS**
   - Stephen applies same mosaic config used for Tumamoc source imagery
   - Inputs: Prediction COGs from Phase 7
   - Output: Seamless buffelgrass distribution mosaic

3. **Quality control**
   - Visual inspection of final mosaic
   - Check for artifacts at tile boundaries
   - Verify spatial accuracy
   - Ground-truth validation if possible

4. **Deliverables to stakeholders**
   - Final buffelgrass distribution map (GeoTIFF/COG)
   - Confidence map
   - Metadata and methodology documentation
   - Web map visualization (optional)

**Deliverables:**
- [ ] Prediction COGs delivered to ADS
- [ ] Final mosaic received and validated
- [ ] Distribution map package for land managers
- [ ] Project documentation and methods

**Documentation:**
- `docs/methodology.md` - Complete methods documentation
- `docs/results_summary.md` - Results and accuracy assessment

---

## Technical Stack

**Infrastructure:**
- **Local (Mac M2 Max)**:
  - k3d: Local Kubernetes cluster
  - Geti (CPU-only): Annotation environment
  - Persistent volume: `~/geti-data`
  
- **Cloud (GCP)**:
  - Compute Engine: VM with NVIDIA T4 GPU (on-demand)
  - K3s: Lightweight Kubernetes on VM
  - Geti (GPU-enabled): Training environment
  - Cloud Storage: Project transfer and backup

**Development Environment:**
- **Mac M2 Max**: Data preprocessing, annotation, SDK scripting
- **Python 3.10+**: Data processing and ML pipeline
- **Rasterio/GDAL**: Geospatial data handling

**Workflow:**
- Local → Annotate → Export → Cloud → Train → Export → Local → Iterate

**Key Python Libraries:**
- `geti-sdk` - Geti platform interaction
- `rasterio` - Geospatial raster I/O
- `rio-cogeo` - COG conversion
- `google-cloud-storage` - GCS interaction
- `opencv-python` - Image processing
- `numpy`, `pandas` - Data manipulation

**Cloud Resources:**
- VM: `n1-standard-8` + NVIDIA Tesla T4 (on-demand, only during training)
- Storage: GCS buckets for COGs, project transfers, and results
- Network: External IP with firewall rules
- **Estimated cost: $10-20 for complete project** (15-30 GPU hours total)
  - vs. $24-36 for always-on cloud
  - vs. $0 GPU but 200+ CPU hours (impractical)

---

## Open Questions & Decisions Needed

### Immediate Decisions:
1. **✅ GPU deployment strategy: Cloud GCP VM with NVIDIA T4**
   - Provides necessary GPU acceleration
   - Cost-effective on-demand usage

2. **Chip size for training?**
   - Need to determine optimal size from Geti docs
   - Recommendation: 1024x1024 as starting point

3. **Image loading strategy: ✅ SDK upload**
   - Upload from Mac to cloud Geti via SDK
   - Use GCS as intermediate storage

4. **GCS bucket configuration?**
   - Bucket name: TBD (e.g., `asdm-buffelgrass`)
   - Regions: us-west1 (match VM region)
   - Structure:
     - `gs://asdm-buffelgrass/source_cogs/`
     - `gs://asdm-buffelgrass/training_chips/`
     - `gs://asdm-buffelgrass/predictions/`
   - Access: Service account for VM, authenticated for Mac

### Future Decisions:
4. **Annotation scope**
   - Binary (buffelgrass vs. background) or multi-class?
   - Include confidence/uncertainty classes?

5. **Seasonal considerations**
   - Single season or multi-season training?
   - Current data: Feb 2023 (Tumamoc), 2024 (Sabino)

6. **Inference infrastructure**
   - Local processing sufficient or need cloud compute?
   - Cost-performance tradeoffs

7. **Validation strategy**
   - Ground-truth data availability?
   - Field validation possible?

---

## Success Metrics

**Technical Metrics:**
- IoU (Intersection over Union) > 0.75
- Pixel accuracy > 90%
- F1-score > 0.80
- False positive rate < 10%

**Operational Metrics:**
- Processing time: < 1 hour per source image for inference
- Model training: < 1 week from annotation start to final model
- Total project timeline: 4-6 weeks

**Deliverable Metrics:**
- Final map delivered in actionable format
- Documentation complete and reproducible
- Pipeline reusable for future imagery

---

## Project Timeline (Estimated)

| Phase | Duration | Dependencies | GPU Hours | Where |
|-------|----------|--------------|-----------|-------|
| 1. Data Preprocessing | 2-3 days | Dropbox access, GCS setup, GCP project | 0 | Mac |
| 2. Chip Generation | 1-2 days | Phase 1 complete | 0 | Mac |
| 3. Geti Setup | 1 day | k3d installed, VM ready (but off) | 0 | Mac + GCP |
| 4. Project Setup | 1 day | Phase 3 complete | 0 | Mac (local) |
| 5. Annotation | 1-2 weeks | Time for annotation | 0 | Mac (local) |
| 6. Training Iteration 1 | 2-3 hours | Annotated data ready | 1-2 | Cloud |
| 7. Training Iteration 2-5 | 1 week | Phase 6 results | 8-15 | Mac → Cloud |
| 8. Full Inference | 2-4 days | Best model selected | 5-10 | Cloud |
| 9. Mosaic & Delivery | 1 week | Coordination with ADS | 0 | Mac + GCS |

**Total estimated time: 4-6 weeks**  
**Total GPU hours: 15-30 hours (~$10-20 in compute costs)**  
**Cloud VM running time: Only during training (~15-30 hours total over 4-6 weeks)**

---

## Risk Assessment

**Technical Risks:**
- GCP VM setup complexity → Mitigation: Detailed setup scripts, SSH-only access simplifies setup
- SSH connectivity issues → Mitigation: Use GCP's built-in SSH, test connection early
- GPU out of memory during training → Mitigation: Monitor VRAM usage, adjust batch sizes
- Persistent volume configuration issues → Mitigation: Test storage before annotation
- SDK script failures → Mitigation: Error handling and retry logic in training scripts
- Model performance insufficient → Mitigation: Active learning, more training data
- Inference scaling challenges → Mitigation: Batch processing, use cloud compute

**Data Risks:**
- Training data not representative → Mitigation: Diverse chip sampling
- Annotation quality inconsistent → Mitigation: Guidelines, QC process
- Seasonal variation in imagery → Mitigation: Multi-season training data

**Coordination Risks:**
- Delays in ADS mosaicing → Mitigation: Early communication, clear deliverables
- GCS access/permissions issues → Mitigation: Set up early, test thoroughly

**Cost Risks:**
- Forgetting to stop VM → Mitigation: Calendar reminders, use preemptible VMs (if suitable)
- Underestimating GPU hours needed → Mitigation: Budget $50 buffer, monitor usage

---

## Next Steps

**Immediate (Week 1):**
1. Set up GCP project and GCS buckets
2. Set up local k3d cluster on Mac
3. Deploy local Geti (CPU-only) for annotation
4. Download Tumamoc source JPEGs from Dropbox
5. Implement COG conversion script and upload COGs to GCS

**Short-term (Weeks 2-3):**
6. Generate training chips (local on Mac)
7. Upload chips to local Geti
8. Begin annotation locally (target 20-30 images)
9. Create GCP VM with GPU (only when ready to train)
10. Export annotated project, import to cloud, and run first training

**Medium-term (Week 3-4):**
11. Export trained model, review results locally
12. Continue annotation iterations locally
13. Periodic training on cloud (stop VM between sessions)

**Medium-term (Weeks 4-6):**
9. Iterate on model performance
10. Full inference pipeline
11. Coordinate with ADS for final mosaicing
12. Deliver final products

---

*This plan is a living document and will be updated as the project progresses.*

**Version:** 1.0  
**Last Updated:** October 29, 2025  
**Status:** Initial planning phase

