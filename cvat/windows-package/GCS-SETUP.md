# GCS Bucket Setup for Training Chips

## Create Training Chips Folder Structure

Run these commands to set up the GCS bucket for storing training chips:

```bash
# Create 1024x1024 training chips directory
gcloud --configuration=asdm storage objects create \
  gs://tumamoc-2023/training_chips/1024x1024/ \
  --content-type=application/x-directory

# Create subdirectories for different chip sizes (if needed)
gcloud --configuration=asdm storage objects create \
  gs://tumamoc-2023/training_chips/raw/ \
  --content-type=application/x-directory

# Create annotations directory for merged results
gcloud --configuration=asdm storage objects create \
  gs://tumamoc-2023/training_annotations/ \
  --content-type=application/x-directory

gcloud --configuration=asdm storage objects create \
  gs://tumamoc-2023/training_annotations/individual/ \
  --content-type=application/x-directory
```

Or using `gsutil` (if directories aren't created automatically on first upload):

```bash
# Touch empty marker files to create directories
echo "" | gcloud --configuration=asdm storage cp - gs://tumamoc-2023/training_chips/.keep
echo "" | gcloud --configuration=asdm storage cp - gs://tumamoc-2023/training_annotations/.keep
echo "" | gcloud --configuration=asdm storage cp - gs://tumamoc-2023/training_annotations/individual/.keep
```

## Upload Training Chips

After generating 1024×1024 chips locally:

```bash
# Upload all chips to GCS
gcloud --configuration=asdm storage cp \
  data/training_chips/*.tif \
  gs://tumamoc-2023/training_chips/1024x1024/ \
  --recursive

# Verify upload
gcloud --configuration=asdm storage ls gs://tumamoc-2023/training_chips/1024x1024/ | wc -l
```

## Download Chips for Annotators

When distributing to annotators:

```bash
# Download chips for specific annotator
mkdir -p buffelgrass-annotation-kaitlyn/chips

# Download all chips (they'll use a subset)
gcloud --configuration=asdm storage cp \
  'gs://tumamoc-2023/training_chips/1024x1024/*.tif' \
  buffelgrass-annotation-kaitlyn/chips/
```

Or download split subsets if you've already divided them:

```bash
# If you've split and uploaded by annotator
gcloud --configuration=asdm storage cp \
  'gs://tumamoc-2023/training_chips/1024x1024/annotator_1/*.tif' \
  buffelgrass-annotation-kaitlyn/chips/
```

## Final Bucket Structure

```
gs://tumamoc-2023/
├── source-jpg/              # Original imagery (977 files, 63 GB) ✅
├── cogs/                    # Cloud-Optimized GeoTIFFs (975 files, 140 GB) ✅
├── training_chips/          # Extracted chips for annotation
│   ├── 1024x1024/          # Standard 1024×1024 square chips
│   └── raw/                # Original extractions (if needed)
├── training_annotations/    # Merged and individual annotations
│   ├── individual/         # Individual annotator exports
│   └── merged_buffelgrass_annotations.json
├── project_exports/         # GETI project exports
├── trained_models/          # Trained model exports
└── predictions/            # Final inference results
```

## Chip Size Decision: 1024×1024 Square

**Recommended**: Use **1024×1024 square chips** for training.

**Rationale:**
- Computer vision models work best with square inputs
- Rotational augmentation maintains aspect ratio
- Clean tensor stacking in batches
- Pre-trained models expect square images
- 1024px is large enough for human annotation comfort
- Modern annotation tools handle square images well

**Not Recommended**: Rectangular chips (e.g., 1200×800)
- Rotations create inconsistent aspect ratios
- Requires padding for batch processing
- May confuse transfer learning from square pre-trained models
- Minimal improvement for human annotators


