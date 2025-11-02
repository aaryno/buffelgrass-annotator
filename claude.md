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

---

*This directory contains all code, data, models, and documentation related to the buffelgrass mapping initiative.*

