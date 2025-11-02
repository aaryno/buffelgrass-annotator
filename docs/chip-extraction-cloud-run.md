# Parallel Chip Extraction with Cloud Run

Extract training chips from all COGs using Cloud Run for maximum speed and automatic organization into folders for parallel annotation.

## Overview

**What it does:**
- Extracts 4 non-overlapping 1024×1024 chips from each COG
- Organizes chips into 10 folders (01-10) for 10-way parallel annotation
- Names chips with `A_` prefix for future expandability (`B_`, `C_` chips)
- Uses 50 parallel Cloud Run workers for fast processing

**Output:**
```
gs://tumamoc-2023/training_chips/1024x1024/
├── 01/
│   ├── A_cap-29792_01.png
│   ├── A_cap-29792_02.png
│   ├── A_cap-29792_03.png
│   ├── A_cap-29792_04.png
│   ├── A_cap-29845_01.png
│   └── ...
├── 02/
│   ├── A_cap-30123_01.png
│   └── ...
...
└── 10/
    └── ...
```

**Expected results:**
- Input: ~975 COGs
- Output: ~3,900 chips (975 × 4)
- Distribution: ~390 chips per folder (balanced)
- Processing time: ~10-15 minutes with 50 parallel workers

## Quick Start

### One Command

```bash
make extract-chips-parallel
```

This will:
1. Build Docker container with chip extraction code
2. Deploy Cloud Run job
3. Execute job with 50 parallel workers
4. Extract and upload all chips to GCS

### Monitor Progress

```bash
# Check job status
gcloud --configuration=asdm run jobs executions list \
  --job chip-extraction \
  --region us-central1

# View logs
gcloud --configuration=asdm logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=chip-extraction" \
  --limit 50
```

### Verify Output

```bash
# Count chips in each folder
for i in {01..10}; do
  count=$(gcloud --configuration=asdm storage ls \
    gs://tumamoc-2023/training_chips/1024x1024/$i/ | grep -c ".png")
  echo "Folder $i: $count chips"
done

# Sample chips from folder 01
gcloud --configuration=asdm storage ls \
  gs://tumamoc-2023/training_chips/1024x1024/01/ \
  | head -20
```

## How It Works

### 1. Folder Assignment

Each COG is consistently hashed to a folder (01-10) based on its filename:

```python
hash_value = md5(filename).hexdigest()
folder_num = (hash_value % 10) + 1  # Results in 01-10
```

This ensures:
- Same COG always goes to same folder
- Even distribution across folders
- Deterministic (can re-run safely)

### 2. Non-Overlapping Chip Extraction

Chips are extracted using grid-based sampling:

```
For 4 chips, divide image into 2×2 grid:

+----------+----------+
|  Chip 1  |  Chip 2  |
|   (TL)   |   (TR)   |
+----------+----------+
|  Chip 3  |  Chip 4  |
|   (BL)   |   (BR)   |
+----------+----------+
```

Each chip:
- 1024×1024 pixels
- Sampled from center of grid cell (with slight randomness)
- Guaranteed no overlap with other chips
- Stays within image boundaries (margin = 10px)

### 3. Naming Convention

Format: `A_{source_name}_{chipnum}.png`

Examples:
- `A_cap-29792_01.png` - COG cap-29792, chip 1
- `A_cap-29792_02.png` - COG cap-29792, chip 2
- `A_tumamoc-west-01_01.png` - COG tumamoc-west-01, chip 1

**Why "A_" prefix?**
- Annotators work through "A" chips first
- If more training data needed later, add "B" chips (different random seeds)
- Keeps annotation progressive: A → B → C
- Alphabetical sorting ensures correct order

### 4. Parallel Processing

Cloud Run job runs 50 parallel tasks:

```
Task 0:  Processes COGs 0, 50, 100, 150, ...
Task 1:  Processes COGs 1, 51, 101, 151, ...
Task 2:  Processes COGs 2, 52, 102, 152, ...
...
Task 49: Processes COGs 49, 99, 149, 199, ...
```

Each task:
- Lists all COGs
- Filters to its assigned subset
- Extracts 4 chips per COG
- Uploads directly to GCS

## Distribution Strategy

### 10 Folders for 10 Annotators

**Ideal setup:**
- 10 annotators
- Each gets 1 folder (~390 chips)
- ~1-2 hours annotation time per person
- All annotate in parallel

**Alternative: 4 Annotators**
- Annotator 1: Folders 01, 02, 03
- Annotator 2: Folders 04, 05, 06
- Annotator 3: Folders 07, 08
- Annotator 4: Folders 09, 10

**Flexible scaling:**
- Combine folders as needed
- Each folder is independent
- Can distribute different amounts per annotator

## Customization

### Change Number of Chips Per COG

Edit `deploy_chip_extraction.sh`:

```bash
--set-env-vars "CHIPS_PER_IMAGE=8"  # Default: 4
```

For 8 chips, uses 3×3 grid (9 cells, samples 8).

### Change Chip Size

```bash
--set-env-vars "CHIP_SIZE=512"  # Default: 1024
```

### Change Number of Folders

Edit `chip_extraction_job.py`:

```python
folder_num = hash_filename_to_folder(filename, num_folders=20)  # Default: 10
```

### Change Parallelism

```bash
./deploy_chip_extraction.sh --tasks 100  # Default: 50
```

More tasks = faster, but:
- Increased costs
- Potential rate limits
- Diminishing returns beyond 100

## Cost Estimation

**Resources per task:**
- Memory: 4 GiB
- CPU: 2 vCPU
- Time: ~15 minutes

**Cost calculation:**
- 50 tasks × 15 min × $0.00001296/vCPU-second × 2 vCPU × 60 sec
- = 50 × 15 × 0.00001296 × 2 × 60
- ≈ $2.33 per run

**One-time cost:** ~$2-3 to generate complete training dataset

## Troubleshooting

### "Image too small for chips"

Some COGs may be smaller than 1024×1024 + margins.

**Solution:** These are automatically skipped with warning in logs.

### "Uneven folder distribution"

With ~975 COGs, folders should have 95-100 chips each (±10%).

If severely uneven:
```bash
# Check actual distribution
for i in {01..10}; do
  echo -n "Folder $i: "
  gcloud --configuration=asdm storage ls \
    gs://tumamoc-2023/training_chips/1024x1024/$i/ | wc -l
done
```

Hash function provides good distribution, but small sample sizes may vary.

### "Job timeout"

Default timeout: 30 minutes per task.

If timing out:
- Reduce parallelism (fewer tasks, each processes more COGs)
- Increase timeout: `--task-timeout 60m`
- Check for slow COGs (large files, many overviews)

### "Missing chips"

Check logs for failed COGs:

```bash
gcloud --configuration=asdm logging read \
  "resource.type=cloud_run_job AND jsonPayload.message=~'Failed'" \
  --limit 100
```

Re-run job - it will skip existing chips and only process missing ones.

## Next Steps

After extraction:

1. **Download chips for annotation:**
   ```bash
   # Download entire folder for annotator
   gcloud --configuration=asdm storage cp \
     'gs://tumamoc-2023/training_chips/1024x1024/01/*' \
     ./buffelgrass-annotation-person1/chips/
   ```

2. **Distribute to annotators:**
   See `cvat/windows-package/DEPLOYMENT.md` for complete workflow

3. **Expand if needed:**
   Run again with `B_` prefix:
   ```bash
   # Edit chip_extraction_job.py:
   chip_name = f"B_{cog_name}_{i+1:02d}.png"
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Run Job                            │
│                 chip-extraction                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 50 parallel tasks
                           ▼
      ┌──────────────────────────────────────────────┐
      │  Task 0   Task 1  ...  Task 48   Task 49    │
      └──────────────────────────────────────────────┘
                           │
                           │ List COGs
                           ▼
           ┌───────────────────────────────┐
           │   gs://tumamoc-2023/cogs/     │
           │   (975 COG files)             │
           └───────────────────────────────┘
                           │
                           │ Read COGs (streaming)
                           │ Extract 4 chips each
                           ▼
    ┌────────────────────────────────────────────┐
    │ gs://tumamoc-2023/training_chips/1024x1024/│
    │  ├── 01/ (390 chips)                       │
    │  ├── 02/ (390 chips)                       │
    │  ...                                        │
    │  └── 10/ (390 chips)                       │
    └────────────────────────────────────────────┘
                           │
                           │ Download by folder
                           ▼
               ┌─────────────────────┐
               │  Windows Annotators │
               │  (10 people)        │
               └─────────────────────┘
```

---

**Questions?** Check the main project docs or run `make help`


