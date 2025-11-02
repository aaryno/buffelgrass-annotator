# Complete Annotation Workflow - 10 Annotators

Quick reference for extracting chips and distributing to 10 parallel annotators using the Windows CVAT package.

## Step 1: Extract Training Chips (One Command)

```bash
make extract-chips-parallel
```

**What this does:**
- Extracts 4 non-overlapping 1024×1024 chips from each COG (~975 COGs)
- Organizes into 10 folders (01-10) using consistent hashing
- Names chips with `A_` prefix (e.g., `A_cap-29792_01.png`)
- Uploads to `gs://tumamoc-2023/training_chips/1024x1024/{01-10}/`
- **Result:** ~3,900 chips, ~390 chips per folder

**Time:** ~10-15 minutes with 50 Cloud Run workers

## Step 2: Download Chips for Each Annotator

```bash
# For annotator 1 (folder 01)
gcloud --configuration=asdm storage cp \
  'gs://tumamoc-2023/training_chips/1024x1024/01/*' \
  ./buffelgrass-annotation-kaitlyn/chips/

# For annotator 2 (folder 02)
gcloud --configuration=asdm storage cp \
  'gs://tumamoc-2023/training_chips/1024x1024/02/*' \
  ./buffelgrass-annotation-person2/chips/

# Repeat for all 10 annotators...
```

Or use a loop:

```bash
ANNOTATORS=("kaitlyn" "person2" "person3" "person4" "person5" "person6" "person7" "person8" "person9" "person10")

for i in {0..9}; do
  folder=$(printf "%02d" $((i+1)))
  annotator=${ANNOTATORS[$i]}
  echo "Downloading folder $folder for $annotator..."
  
  mkdir -p ./buffelgrass-annotation-$annotator/chips
  gcloud --configuration=asdm storage cp \
    "gs://tumamoc-2023/training_chips/1024x1024/$folder/*" \
    "./buffelgrass-annotation-$annotator/chips/"
done
```

## Step 3: Package for Windows Annotators

For each annotator:

```bash
# Copy CVAT Windows package
cp -r cvat/windows-package/ buffelgrass-annotation-kaitlyn/

# Chips already downloaded in Step 2
# (should be in buffelgrass-annotation-kaitlyn/chips/)

# Create annotator info file
cat > buffelgrass-annotation-kaitlyn/ANNOTATOR_INFO.txt << EOF
Annotator: Kaitlyn
Folder: 01
Assigned chips: ~390 images
Expected time: 1-2 hours
Coordinator: [Your name]
Email: [Your email]
EOF

# Zip for distribution
zip -r buffelgrass-annotation-kaitlyn.zip buffelgrass-annotation-kaitlyn/
```

## Step 4: Distribute to Annotators

**Via USB Drive (Recommended):**
```bash
# Copy each ZIP to USB
cp buffelgrass-annotation-*.zip /Volumes/USB_DRIVE/
```

**Via Cloud Storage:**
```bash
# Upload to shared folder
gcloud --configuration=asdm storage cp \
  buffelgrass-annotation-kaitlyn.zip \
  gs://tumamoc-2023/annotation-packages/
```

Include instructions: `cvat/windows-package/README.md`

## Step 5: Annotators Work (1-2 Hours Each)

Each annotator:
1. Extract ZIP to `Documents/buffelgrass-annotation/`
2. Double-click `start-cvat.bat`
3. Register account at http://localhost:8080
4. Run: `python setup-project.py --username [their_name]`
5. Annotate all ~390 chips (focus on buffelgrass)
6. Export as COCO 1.0 format
7. Send ZIP back to coordinator

## Step 6: Collect Exports

Annotators send back files like:
- `buffelgrass_annotations_kaitlyn.zip`
- `buffelgrass_annotations_person2.zip`
- ... (10 total)

```bash
# Create collection folder
mkdir -p data/annotation_exports

# Extract each export
cd data/annotation_exports
unzip buffelgrass_annotations_kaitlyn.zip -d kaitlyn
unzip buffelgrass_annotations_person2.zip -d person2
# ... etc for all 10

# Copy COCO JSON files to root
cp kaitlyn/annotations/instances_default.json kaitlyn_annotations.json
cp person2/annotations/instances_default.json person2_annotations.json
# ... etc
```

## Step 7: Merge All Annotations

```bash
cd ~/asdm

python scripts/merge_coco_annotations.py \
  data/annotation_exports/kaitlyn_annotations.json \
  data/annotation_exports/person2_annotations.json \
  data/annotation_exports/person3_annotations.json \
  data/annotation_exports/person4_annotations.json \
  data/annotation_exports/person5_annotations.json \
  data/annotation_exports/person6_annotations.json \
  data/annotation_exports/person7_annotations.json \
  data/annotation_exports/person8_annotations.json \
  data/annotation_exports/person9_annotations.json \
  data/annotation_exports/person10_annotations.json \
  -o data/merged_buffelgrass_annotations.json \
  --verify
```

**Expected output:**
```
✅ Total images: 3,900
✅ Total annotations: [varies]
✅ Avg per image: [varies]
```

## Step 8: Upload to GCS

```bash
# Upload merged annotations
gcloud --configuration=asdm storage cp \
  data/merged_buffelgrass_annotations.json \
  gs://tumamoc-2023/training_annotations/

# Backup individual exports
gcloud --configuration=asdm storage cp \
  data/annotation_exports/*.json \
  gs://tumamoc-2023/training_annotations/individual/
```

## Step 9: Train Model (Next Phase)

Proceed with GETI training using the merged annotations.

See: `docs/remote-training-via-sdk.md`

---

## Quick Commands Summary

```bash
# 1. Extract chips
make extract-chips-parallel

# 2. Download all folders
for i in {01..10}; do
  mkdir -p ./chips-folder-$i
  gcloud --configuration=asdm storage cp \
    "gs://tumamoc-2023/training_chips/1024x1024/$i/*" \
    "./chips-folder-$i/"
done

# 3. Package for Windows (see Step 3 above)

# 4. Distribute (USB or cloud)

# 5. Collect exports when complete

# 6. Merge all
python scripts/merge_coco_annotations.py \
  data/annotation_exports/*_annotations.json \
  -o data/merged_buffelgrass_annotations.json \
  --verify

# 7. Upload to GCS
gcloud --configuration=asdm storage cp \
  data/merged_buffelgrass_annotations.json \
  gs://tumamoc-2023/training_annotations/
```

---

## Timeline Estimate

| Phase | Time | Notes |
|-------|------|-------|
| Extract chips | 10-15 min | Cloud Run (automated) |
| Download & package | 30-45 min | Per annotator setup |
| Distribution | Varies | USB drive or file transfer |
| Annotation | 1-2 hours | Per annotator (parallel) |
| Collection | 15 min | Gather exports |
| Merging | 2 min | Automated |
| Upload | 1 min | To GCS |
| **Total** | **2-3 hours** | **End-to-end (with 10 parallel annotators)** |

**Single annotator:** Would take 10-20 hours for all 3,900 chips
**10 parallel annotators:** Each does ~390 chips in 1-2 hours

---

## Troubleshooting

### Uneven folder distribution?

Check actual distribution:
```bash
for i in {01..10}; do
  echo -n "Folder $i: "
  gcloud --configuration=asdm storage ls \
    gs://tumamoc-2023/training_chips/1024x1024/$i/ | wc -l
done
```

Should be ~390 ±10% per folder.

### Need more training data?

Extract "B_" chips with different sampling:

```bash
# Edit chip_extraction_job.py line ~170:
chip_name = f"B_{cog_name}_{i+1:02d}.png"

# Re-deploy and run
cd scripts/cloudrun && ./deploy_chip_extraction.sh --execute
```

This adds another ~3,900 chips without duplicating any.

### Annotator can't run Docker?

- Requires Docker Desktop with WSL2
- Admin rights needed for installation
- Windows 10/11 required
- Alternative: Use cloud-hosted CVAT instance

---

**Questions?** See:
- `cvat/windows-package/README.md` - Annotator guide
- `cvat/windows-package/DEPLOYMENT.md` - Coordinator guide  
- `docs/chip-extraction-cloud-run.md` - Technical details


