# ASDM Buffelgrass Mapping Project

Machine learning-based buffelgrass detection and mapping for southern Arizona using aerial imagery and computer vision.

## Overview

This project aims to produce actionable buffelgrass distribution maps to support invasive species management efforts in the Sonoran Desert region. Buffelgrass (*Pennisetum ciliare*) is an invasive grass species that poses significant threats to native ecosystems by increasing fire frequency and intensity.

## Technical Stack

- **Imagery**: Bespoke 3-band aerial imagery from Air Data Solutions
- **Cloud**: GCP (`asdm-399400` project)
- **Storage**: Cloud-Optimized GeoTIFFs in `gs://tumamoc-2023`
- **Annotation**: CVAT for semantic segmentation
- **ML Platform**: GETI (Intel's computer vision platform)

## Workflow

1. Convert source imagery to Cloud-Optimized GeoTIFFs
2. Generate training chips via windowed sampling (29,280 chip windows across 976 COGs)
3. Annotate training data using CVAT
4. Train segmentation model using GETI
5. Apply model to full source imagery
6. Deliver prediction maps to land managers

## Quick Start

```bash
make help                       # Show all available commands
make extract-chips-parallel     # Extract 4 chips per COG → 10 folders (Cloud Run)
make cvat-complete-setup        # Install CVAT + create project + upload images
make cvat-status                # Check CVAT status
```

## GCP Resources

- **Project**: `asdm-399400` (account: `aaryno@gmail.com`)
- **Bucket**: `gs://tumamoc-2023`
- **Config**: `asdm` (use `gcloud --configuration=asdm`)

**Key Bucket Paths:**
- `gs://tumamoc-2023/source-jpg/` - Original imagery (977 files, 63 GB)
- `gs://tumamoc-2023/cogs/` - Cloud-Optimized GeoTIFFs (976 files, 140 GB)
- `gs://tumamoc-2023/chip-manifest.csv` - Master chip manifest (29,280 windows)
- `gs://tumamoc-2023/training_chips/1024x1024/` - Extracted chips for annotation

## Project Structure

- `scripts/` - Data processing and ML pipeline scripts
  - `cloudrun/` - Cloud Run Jobs for parallel processing
- `cvat/` - Annotation tool setup and deployment
  - `windows-package/` - Windows deployment for collaborative annotation
- `docs/` - Technical documentation
  - `chip-extraction-cloud-run.md` - Parallel chip extraction
  - `cvat-windows-setup.md` - Windows CVAT setup
  - `collaborative-annotation-workflow.md` - Multi-person annotation
  - `local-geti-setup.md` - Local GETI deployment
  - `remote-training-via-sdk.md` - SSH + SDK training workflow
- `k8s/` - Kubernetes configuration for local GETI
- `tests/` - Test scripts

## Documentation

See [`claude.md`](claude.md) for detailed project context and [`project-plan-detailed.md`](project-plan-detailed.md) for complete implementation details.

## Setup

1. Configure GCP credentials:
   ```bash
   gcloud --configuration=asdm auth login
   ```

2. Install Python dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. See [`SETUP-GCS-CREDENTIALS.md`](SETUP-GCS-CREDENTIALS.md) for detailed GCS setup.

## Data Pipeline

The chip manifest contains 29,280 potential training chips organized into 625 bins (AA-YY) for flexible sampling:
- **976 COGs** × 30 chips each (6×5 non-overlapping grid)
- **Format**: `chip_path,source_image,ulx,uly,width,height`
- Sample chips by bin to avoid overlap between annotation batches

---

*This project supports invasive species management efforts in the Sonoran Desert region through advanced computer vision and geospatial analysis.*

