# ASDM Buffelgrass Mapping Project

## Overview
Machine learning-based buffelgrass detection and mapping project for southern Arizona using aerial imagery and computer vision.

## Project Goal
Produce actionable buffelgrass distribution maps to support invasive species management efforts in the Sonoran Desert region.

## Technical Approach

### Data Source
- **Provider**: Air Data Solutions
- **Imagery Type**: Bespoke 3-band aerial imagery
- **Coverage**: Southern Arizona

### Cloud Infrastructure
- **GCP Project**: `asdm-399400` (account: aaryno@gmail.com)
- **GCS Bucket**: `tumamoc-2023`
- **gcloud Configuration**: `asdm` (use `gcloud --configuration=asdm` for all commands)
- **gcloud Path**: `/opt/homebrew/share/google-cloud-sdk/bin/gcloud` (add to PATH or use full path in scripts)

### Model Development
- **Platform**: GETI (Intel's computer vision platform)
- **Task Type**: Semantic segmentation
- **Target**: Buffelgrass (*Pennisetum ciliare*) identification

## Background
Buffelgrass is an invasive grass species that poses significant threats to native Sonoran Desert ecosystems by increasing fire frequency and intensity. Accurate mapping is critical for targeted management and eradication efforts.

## Workflow

See [`project-plan.md`](project-plan.md) for high-level project plan or [`project-plan-detailed.md`](project-plan-detailed.md) for complete implementation details.

**High-level workflow:**
1. Acquire 3-band aerial imagery from Air Data Solutions
2. Convert to Cloud-Optimized GeoTIFFs and upload to GCP (`make convert-cogs-parallel`)
3. Generate training chips via windowed sampling (`make extract-chips`)
4. Annotate training data for buffelgrass presence using CVAT (`make cvat-complete-setup`)
5. Build and train segmentation model
6. Apply model to full source imagery
7. Deliver prediction maps to land managers and conservation organizations

**Quick start:**
```bash
make help                       # Show all available commands
make extract-chips-parallel     # Extract 4 chips per COG → 10 folders (Cloud Run)
make cvat-complete-setup        # Install CVAT locally + create project + upload images
make cvat-vm-deploy             # Deploy CVAT to cloud VM (one-time setup)
make cvat-vm-start              # Start cloud VM (~2 min boot)
make cvat-vm-stop               # Stop cloud VM (saves money, preserves data)
```

## Project Structure

- `data/` - Data sources and documentation
- `project-plan-detailed.md` - Detailed implementation plan
- `docs/` - Technical documentation
  - `chip-extraction-cloud-run.md` - Parallel chip extraction into 10 folders for multi-annotator workflows
  - `cvat-windows-setup.md` - Complete Windows setup guide for CVAT
  - `collaborative-annotation-workflow.md` - Multi-person annotation workflow
  - `local-geti-setup.md` - Complete guide for running GETI locally
  - `remote-training-via-sdk.md` - SSH + SDK training workflow (no web UI needed)
- `scripts/` - Data processing and ML pipeline scripts
  - `dropbox_to_gcs.py` - Dropbox → GCS transfer (Cloud Run, 50 workers, with pagination)
  - `convert_to_cogs.py` - JPEG → COG conversion
  - `chip_extractor.py` - Extract training chips from COGs
  - `split_dataset_by_region.py` - Split chips for parallel annotation
  - `merge_coco_annotations.py` - Merge COCO annotations from multiple annotators
  - `cloudrun/` - Cloud Run Jobs for parallel processing (50x speedup)
    - `chip_extraction_job.py` - Extract 4 chips per COG into 10 folders (3,900 total chips)
- `notebooks/` - Analysis and exploration notebooks
- `k8s/` - Kubernetes configuration
  - `k3d-local-setup.sh` - Automated k3d cluster setup for local GETI
- `geti/` - GETI platform source code (Intel's CV platform)
- `geti-sdk/` - GETI Python SDK and example notebooks
- `geti-vm/` - Cloud VM deployment for GETI instance
- `cvat/` - Lightweight annotation tool setup for segmentation tasks
  - `windows-package/` - Production-ready Windows deployment for 4-person collaborative annotation
  - `export-project.py` - Export COCO annotations from CVAT projects
- `cvat-vm/` - Cloud VM deployment for CVAT (cost-effective, start/stop as needed)
  - `terraform/` - Infrastructure as Code for GCP VM deployment
  - `scripts/` - VM management scripts (start, stop, status, backup, ssh)
  - `DEPLOYMENT-GUIDE.md` - Step-by-step deployment instructions

## GCP Resources

**Project ID:** `asdm-399400`  
**Account:** `aaryno@gmail.com`  
**Primary Bucket:** `gs://tumamoc-2023`  
**gcloud config:** `asdm` (authenticated and configured)

**Bucket Structure:**
- `gs://tumamoc-2023/source-jpg/` - Original imagery from Dropbox (977 files, 63 GB) ✅
- `gs://tumamoc-2023/cogs/` - Cloud-Optimized GeoTIFFs (976 files, 140 GB) ✅
- `gs://tumamoc-2023/chip-manifest.csv` - Master manifest: 29,280 chip windows across 625 bins ✅
- `gs://tumamoc-2023/chip_manifests/partial/` - Partial manifests from Cloud Run tasks ✅
- `gs://tumamoc-2023/training_chips/1024x1024/` - Extracted 1024×1024 chips for annotation
- `gs://tumamoc-2023/training_annotations/` - Merged COCO annotations from all annotators
- `gs://tumamoc-2023/training_annotations/individual/` - Individual annotator exports (backups)
- `gs://tumamoc-2023/project_exports/` - Geti project exports (local → cloud)
- `gs://tumamoc-2023/trained_models/` - Trained model exports (cloud → local)
- `gs://tumamoc-2023/predictions/` - Final inference results

**Chip Manifest Details:**
- **976 COGs** × 30 chips each (6×5 non-overlapping grid) = **29,280 total chip windows**
- **625 bins** (AA-YY) for flexible sampling and spatial control
- **Format:** `chip_path,source_image,ulx,uly,width,height`
- **Example:** `rf/rf-cap-30704.png,cap-30704,1323,712,1024,1024`
- **Usage:** Sample chips by bin to avoid overlap between annotation batches

## Annotation Workflow

### Two Chip Extraction Strategies

**Workflow 1: Chip Manifest System (CURRENT)**
- **Purpose**: Pre-compute ALL possible chip locations for selective sampling
- **Strategy**: 6×5 grid = **30 chips per COG**
- **Binning**: 625 bins (AA-YY) via MD5 hash for even distribution
- **Naming**: `{bin}-{randomtoken}-{imagename}.png` (e.g., `bt-ef-cap-29792.png`)
- **Folders**: Organized by bin (`aa/`, `ab/`, ..., `yy/`)
- **Total**: 29,280 chip **windows** pre-computed in `chip-manifest.csv`
- **Extraction**: Use `make extract-chips-for-annotation BIN=rf COUNT=1000` to selectively extract
- **Advantage**: Precise control over which chips to annotate, avoid overlap between annotators

**Workflow 2: Direct Chip Extraction (DEPRECATED)**
- **Purpose**: Extract actual training chips immediately without manifest
- **Strategy**: 4 non-overlapping chips per COG
- **Binning**: 10 bins (01-10) via MD5 hash
- **Naming**: `A_{cogname}_{chipnum}.png` (e.g., `A_cap-29799_01.png`)
- **Status**: ❌ Deleted 3,904 chips on Nov 2, 2025 - switching to workflow 1

### Annotation Binning Plan (4 Annotators)

**Bin Allocation Strategy:**
- **625 total bins** (AA through YY)
- Each bin contains ~47 chips on average
- Assign distinct bin groups to each annotator to prevent overlap

**Proposed Allocation:**

| Annotator | Bin Range | Bin Examples | Est. Chips (1K each) |
|-----------|-----------|--------------|----------------------|
| 1         | AA-GY     | aa, ab, ..., gy | ~1,000 |
| 2         | HA-MY     | ha, hb, ..., my | ~1,000 |
| 3         | NA-TY     | na, nb, ..., ty | ~1,000 |
| 4         | UA-YY     | ua, ub, ..., yy | ~1,000 |

**Total**: 4,000 chips for annotation (sufficient for initial model training)

**Extraction Commands:**
```bash
# Annotator 1: Extract first 1000 chips from bins AA-GY
grep -E '^[a-g][a-y]/' chip-manifest.csv | head -1000 > annotator1.csv
make extract-chips-for-annotation BIN=aa COUNT=250
make extract-chips-for-annotation BIN=ab COUNT=250
# ... continue for other bins

# Or extract directly from manifest (recommended)
python scripts/extract_chips_from_manifest.py --bin aa --count 1000 --output-dir chips_annotator1/
```

### First Annotation Batch (20 Random Groups)

**Selected Groups for Initial Annotation (Nov 2, 2025):**

These 20 randomly selected 2-letter groups will be our first annotation sets:

```
ah, bt, dx, ej, ev, gx, il, kg, lt, ni, pd, ra, rb, tr, vc, vq, vt, wk, xi, yo
```

**Distribution across annotators (5 groups each):**

| Annotator | Groups | Est. Chips |
|-----------|--------|------------|
| aaryn     | ah, bt, dx, ej, ev | ~235 chips |
| kim       | gx, il, kg, lt, ni | ~235 chips |
| stephen   | pd, ra, rb, tr, vc | ~235 chips |
| kaitlyn   | vq, vt, wk, xi, yo | ~235 chips |

**Total**: ~940 chips for first annotation round

**Extraction Command:**
```bash
# Extract chips for all 20 groups from manifest
python scripts/extract_from_manifest.py --groups ah,bt,dx,ej,ev,gx,il,kg,lt,ni,pd,ra,rb,tr,vc,vq,vt,wk,xi,yo --output gs://tumamoc-2023/training_chips/1024x1024/
```

**Label Definitions (3-class simplified):**
- `buffelgrass` - Target invasive species (RED)
- `other_grass` - Native grasses that could be confused with buffelgrass (YELLOW)
- `background` - Everything else: soil, roads, buildings, vegetation (GRAY)

## CVAT Annotation System

**VM Details:**
- **VM Name**: `cvat-annotation-vm`
- **Zone**: `us-west1-b`
- **URL**: http://35.203.139.174:8080
- **GCP Project**: `asdm-399400`

**VM Management:**
```bash
# Start VM (takes ~2 minutes)
gcloud --configuration=asdm compute instances start cvat-annotation-vm --zone=us-west1-b

# Stop VM (saves money, preserves all data)
gcloud --configuration=asdm compute instances stop cvat-annotation-vm --zone=us-west1-b

# Check VM status
gcloud --configuration=asdm compute instances describe cvat-annotation-vm --zone=us-west1-b --format="value(status)"

# SSH into VM
gcloud --configuration=asdm compute ssh cvat-annotation-vm --zone=us-west1-b
```

**CVAT Management (on VM):**
```bash
cd /mnt/cvat-data/cvat

# Check CVAT status
sudo docker-compose ps

# Start CVAT services
sudo docker-compose up -d

# Stop CVAT services
sudo docker-compose down

# Restart specific service
sudo docker-compose restart cvat_server

# View logs
sudo docker-compose logs -f cvat_server

# If redis_ondisk crashes (corrupted data):
sudo docker-compose down
sudo docker volume rm cvat_cvat_cache_db
sudo docker volume create cvat_cvat_cache_db
sudo docker-compose up -d
```

**CVAT Users:**
- **aaryno** / 1976Weather1! (admin - can see all tasks)
- **kim** / ASDM88buffel!
- **stephen** / ASDM88buffel!
- **kaitlyn** / ASDM88buffel!

**Note**: Email sent to Kim, Stephen, and Kaitlyn on Nov 2, 2025 with access instructions and annotation tutorial. VM will remain running for initial testing period (few days).

**CVAT Project:**
- **Name**: "Buffelgrass Detection - 3 Class"
- **Project ID**: 2
- **Tasks**: 20 tasks (5 per annotator)
- **Chips Location**: `/mnt/training_chips/{group}/` (mounted in CVAT containers)

**Task Organization:**
- Tasks named by annotator: "Aaryn - AH", "Kim - GX", etc.
- All tasks visible to aaryno (admin user)
- Other users can see all tasks but should work on their assigned ones

## 🎯 Current Status (Nov 2, 2025) - ANNOTATION READY! 🎉

**✅ SYSTEM FULLY OPERATIONAL - All 20 Tasks Created and Ready**

**COMPLETED SETUP:**
1. ✅ Extracted 1,034 chips from GCS to VM `/mnt/cvat-data/training_chips/`
2. ✅ Created CVAT project "Buffelgrass Detection - 3 Class" (Project ID: 2)
3. ✅ Created 4 user accounts (aaryno, kim, stephen, kaitlyn)
4. ✅ Created all 20 annotation tasks using `cvat-sdk` v2.20.0
5. ✅ Verified all tasks have images and jobs ready
6. ✅ Sent email to Kim, Stephen, and Kaitlyn with instructions
7. ✅ VM running and accessible at http://35.203.139.174:8080

**📋 All 20 Tasks Successfully Created:**

| Task ID | Name | Assignee | Images | Status |
|---------|------|----------|--------|--------|
| 28 | Aaryn - AH | aaryno | 47 | ✅ Ready |
| 29 | Aaryn - BT | aaryno | 62 | ✅ Ready |
| 30 | Aaryn - DX | aaryno | 50 | ✅ Ready |
| 31 | Aaryn - EJ | aaryno | 49 | ✅ Ready |
| 32 | Aaryn - EV | aaryno | 59 | ✅ Ready |
| 33 | Kim - GX | kim | 53 | ✅ Ready |
| 34 | Kim - IL | kim | 57 | ✅ Ready |
| 35 | Kim - KG | kim | 56 | ✅ Ready |
| 36 | Kim - LT | kim | 68 | ✅ Ready |
| 37 | Kim - NI | kim | 40 | ✅ Ready |
| 38 | Stephen - PD | stephen | 36 | ✅ Ready |
| 39 | Stephen - RA | stephen | 52 | ✅ Ready |
| 40 | Stephen - RB | stephen | 51 | ✅ Ready |
| 41 | Stephen - TR | stephen | 56 | ✅ Ready |
| 42 | Stephen - VC | stephen | 38 | ✅ Ready |
| 43 | Kaitlyn - VQ | kaitlyn | 54 | ✅ Ready |
| 44 | Kaitlyn - VT | kaitlyn | 51 | ✅ Ready |
| 45 | Kaitlyn - WK | kaitlyn | 45 | ✅ Ready |
| 46 | Kaitlyn - XI | kaitlyn | 55 | ✅ Ready |
| 47 | Kaitlyn - YO | kaitlyn | 55 | ✅ Ready |

**Total: 1,034 chips across 20 tasks**

**Chip Distribution by Annotator:**
- **Aaryn**: 267 chips (AH, BT, DX, EJ, EV)
- **Kim**: 274 chips (GX, IL, KG, LT, NI)
- **Stephen**: 233 chips (PD, RA, RB, TR, VC)
- **Kaitlyn**: 260 chips (VQ, VT, WK, XI, YO)

**✅ WORKING METHOD CONFIRMED:**
- Use `cvat-sdk` v2.20.0 with `ResourceType.LOCAL`
- Connect to VM via external IP: http://35.203.139.174:8080
- Upload images directly from VM filesystem paths
- SDK handles all metadata, manifests, and chunk creation automatically

**NEXT STEPS:**
1. Wait for annotators to test and provide feedback
2. Begin annotation work (each person has ~230-270 chips)
3. Export annotations when batches are complete
4. Merge COCO annotations from all annotators
5. Begin model training in GETI

## Technical Implementation Details

### Chip Extraction
- Script: `scripts/extract_selected_groups.py`
- Source: `gs://tumamoc-2023/cogs/*.tif`
- Manifest: `chip-manifest.csv` (29,282 total possible chips)
- Selected: 20 groups from manifest (ah, bt, dx, ej, ev, gx, il, kg, lt, ni, pd, ra, rb, tr, vc, vq, vt, wk, xi, yo)
- Output: `/mnt/cvat-data/training_chips/{group}/` on VM

### CVAT Setup
- **Version**: v2.20.0
- **Deployment**: Docker Compose on GCP VM
- **Data Mount**: `/mnt/cvat-data/training_chips:/mnt/training_chips:ro` (read-only)
- **Persistent Storage**: `/mnt/cvat-data/` (50GB disk, survives VM restarts)

### Image Upload Method
Due to SDK/API compatibility issues with CVAT v2.20.0, images were uploaded via Django ORM:

```python
# On VM, inside cvat_server container:
from cvat.apps.engine.models import Task, Data, Image, StorageMethodChoice, StorageChoice
import glob

# Create Data object
data_obj = Data.objects.create(
    chunk_size=72,
    size=len(image_files),
    image_quality=70,
    storage_method=StorageMethodChoice.FILE_SYSTEM,
    storage=StorageChoice.LOCAL
)

# Create Image objects
for idx, img_path in enumerate(image_files):
    Image.objects.create(
        data=data_obj,
        frame=idx,
        path=img_path,
        width=1024,
        height=1024
    )
```

### Job Creation Method
Jobs were created manually via Django ORM due to normal task creation flow not triggering:

```python
# On VM, inside cvat_server container:
from cvat.apps.engine.models import Task, Job, Segment, StatusChoice

segment = Segment.objects.create(
    task=task,
    start_frame=0,
    stop_frame=task.data.size - 1
)

job = Job.objects.create(
    segment=segment,
    status=StatusChoice.ANNOTATION,
    assignee=task.assignee
)
```

### Docker Volume Configuration
Modified `cvat-vm/cvat/docker-compose.yml` to include training chips mount in relevant services:
- `cvat_server`
- `cvat_worker_import`
- `cvat_worker_export`
- `cvat_worker_annotation`

Added volume mount: `- /mnt/cvat-data/training_chips:/mnt/training_chips:ro`

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: CVAT stuck "Connecting..." or 502/504 errors**
- Cause: `cvat_redis_ondisk` service crashing due to corrupted data
- Solution:
```bash
cd /mnt/cvat-data/cvat
sudo docker-compose down
sudo docker volume rm cvat_cvat_cache_db
sudo docker volume create cvat_cvat_cache_db
sudo docker-compose up -d
# Wait 60 seconds for initialization
```

**Issue: Tasks created but no images or jobs**
- Cause: CVAT SDK/API incompatibilities with v2.20.0
- Solution: Use Django ORM directly (see "Technical Implementation Details" above)
- Access Django shell: `sudo docker-compose exec cvat_server python manage.py shell`

**Issue: Images uploaded but no jobs visible**
- Cause: Job creation doesn't happen automatically in all cases
- Solution: Manually create Segment and Job objects via Django ORM (see above)

**Issue: Task assignee filter not working**
- Cause: Tasks created without `assignee` field set
- Solution: Update task assignees via Django:
```python
from cvat.apps.engine.models import Task
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='aaryno')
task = Task.objects.get(id=1)
task.assignee = user
task.save()
```

**Issue: VM data lost after restart**
- Cause: Data stored in ephemeral disk instead of persistent disk
- Solution: All data should be in `/mnt/cvat-data/` which is mounted from persistent disk
- Verify: `df -h /mnt/cvat-data` should show `/dev/sdb` (persistent disk)

### Monitoring Commands

```bash
# Check all services status
cd /mnt/cvat-data/cvat && sudo docker-compose ps

# Check redis_ondisk health (common failure point)
sudo docker-compose logs --tail=50 cvat_redis_ondisk

# Check server logs
sudo docker-compose logs --tail=100 cvat_server

# Check worker logs
sudo docker-compose logs --tail=50 cvat_worker_import

# Verify image files exist
ls -lh /mnt/cvat-data/training_chips/ah/ | head

# Check database status via Django
sudo docker-compose exec cvat_server python manage.py shell -c "from cvat.apps.engine.models import Task; print(f'Tasks: {Task.objects.count()}')"
```

## Next Steps for Annotators

1. **Access CVAT**: http://35.203.139.174:8080
2. **Login** with provided credentials
3. **Filter tasks**: Click "Assigned to me" to see your 5 tasks
4. **Start annotating**:
   - Click on a task
   - Click "Job #1"
   - Use annotation tools to label:
     - 🔴 **buffelgrass** - Target invasive species
     - 🟡 **other_grass** - Native grasses that might be confused
     - ⚫ **background** - Everything else
5. **Save progress**: Ctrl+S or click "Save" regularly
6. **Submit**: Mark job as "Completed" when done

## Cost Management

**VM Running Costs:**
- **n1-standard-2** (2 vCPUs, 7.5 GB RAM): ~$48/month = **$1.58/day** when running 24/7
- **Persistent disk** (50GB): ~$2/month (always charged, even when VM is stopped)
- **Static IP**: ~$7/month (only charged when VM is stopped; free while running)

**Current Status**: VM running for initial testing period (few days) - estimated cost: **~$5-8**

**Cost Reduction Strategy:**
- Stop VM when not actively annotating: `gcloud --configuration=asdm compute instances stop cvat-annotation-vm --zone=us-west1-b`
- All data persists on `/mnt/cvat-data/` when stopped
- Restart when needed (takes ~2 minutes): `gcloud --configuration=asdm compute instances start cvat-annotation-vm --zone=us-west1-b`
- Typical annotation workflow: Run VM for 1-2 weeks during active annotation, then stop until next batch

---

*This directory contains all code, data, models, and documentation related to the buffelgrass mapping initiative.*

