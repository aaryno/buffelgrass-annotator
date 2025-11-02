# Distribution Guide: Packaging CVAT for Collaborators

## Quick Start

To package everything for a collaborator, just run:

```bash
cd /Users/aaryn/asdm
./scripts/package_for_collaborator.sh
```

This interactive script will:
1. Ask for annotator name (e.g., "kaitlyn")
2. Ask which bin to extract (e.g., "aa", "rf", "xy")
3. Ask how many chips (default: 500)
4. Extract chips from COGs based on the manifest
5. Package everything into a ready-to-share folder
6. Optionally create a ZIP file

## What Gets Packaged

The script creates a folder structure like this:

```
ASDM-Annotation-Package-kaitlyn/
├── README.txt              (Setup instructions for collaborator)
├── CHECKLIST.txt           (Annotation workflow checklist)
├── cvat-docker/            (Complete CVAT setup for Windows)
│   ├── start-cvat.bat      ⭐ Main file they double-click
│   ├── stop-cvat.bat
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── setup-project.py
│   ├── README.md
│   └── GCS-SETUP.md
├── chips/                  (500 extracted chip images as PNGs)
│   ├── aa-sn-cap-29814.png
│   ├── aa-tm-cap-29821.png
│   └── ...
└── project/                (For shared project config - optional)
```

## Manual Workflow (Step-by-Step)

If you prefer to do it manually:

### 1. Extract Chips from a Bin

```bash
cd /Users/aaryn/asdm
source venv/bin/activate

# Extract 500 chips from bin 'aa'
make extract-chips-for-annotation BIN=aa COUNT=500

# Or use the script directly:
python3 scripts/extract_chips_from_manifest.py \
    --bin aa \
    --count 500 \
    --output-dir chips_aa/
```

### 2. Create Package Directory

```bash
mkdir -p ASDM-Annotation-Package-kaitlyn/{cvat-docker,chips,project}
```

### 3. Copy Files

```bash
# Copy CVAT files
cp cvat/windows-package/* ASDM-Annotation-Package-kaitlyn/cvat-docker/

# Copy extracted chips
cp chips_aa/* ASDM-Annotation-Package-kaitlyn/chips/
```

### 4. Package and Share

```bash
# Create ZIP
zip -r ASDM-Annotation-Package-kaitlyn.zip ASDM-Annotation-Package-kaitlyn/

# Or upload to Google Cloud Storage
gcloud --configuration=asdm storage cp -r \
    ASDM-Annotation-Package-kaitlyn/ \
    gs://tumamoc-2023/annotation-packages/kaitlyn/
```

## Sharing Options

### Option A: File Sharing Services
- **Google Drive**: Upload ZIP, share link
- **Dropbox**: Upload folder, share link
- **WeTransfer**: For one-time large file transfers
- **USB Drive**: For local/offline delivery

### Option B: Google Cloud Storage (Recommended)

```bash
# Upload package
gcloud --configuration=asdm storage cp -r \
    ASDM-Annotation-Package-kaitlyn/ \
    gs://tumamoc-2023/annotation-packages/kaitlyn/

# Create signed URL (valid for 7 days)
gcloud --configuration=asdm storage sign-url \
    gs://tumamoc-2023/annotation-packages/kaitlyn/ASDM-Annotation-Package-kaitlyn.zip \
    --duration=7d
```

Send the signed URL to your collaborator.

## Chip Selection Strategy

### Random Sampling by Bin
With 625 bins (AA-YY) containing ~47 chips each:

**For 4 annotators:**
- Annotator 1: bins aa-fz (150 bins × ~47 chips = ~7,000 chips)
- Annotator 2: bins ga-lz (150 bins × ~47 chips = ~7,000 chips)  
- Annotator 3: bins ma-rz (150 bins × ~47 chips = ~7,000 chips)
- Annotator 4: bins sa-yy (175 bins × ~47 chips = ~7,000 chips)

**Or extract specific counts from individual bins:**
```bash
# Annotator 1: 500 chips from bin 'aa'
make extract-chips-for-annotation BIN=aa COUNT=500

# Annotator 2: 500 chips from bin 'rf'
make extract-chips-for-annotation BIN=rf COUNT=500
```

### Progressive Annotation
Start with a small test batch:

```bash
# Phase 1: Test with 50 chips
make extract-chips-for-annotation BIN=aa COUNT=50

# After verification, expand to full set
make extract-chips-for-annotation BIN=aa COUNT=500
```

## Email Template

```
Subject: ASDM Tumamoc Hill Vegetation Annotation

Hi [Name],

Thanks for helping with the Tumamoc Hill vegetation mapping project!

**Download Package:** [insert link]

**Setup (15 minutes first time):**

1. Install Docker Desktop:
   https://docs.docker.com/desktop/setup/install/windows-install/

2. Extract the ZIP to: C:\Users\YourName\ASDM\

3. Double-click: cvat-docker\start-cvat.bat
   (First run takes 10-15 minutes)

4. Open browser: http://localhost:8080

5. Create account and start annotating!

**Your Task:**
- Annotate [500] images in the chips/ folder
- Focus on these classes: [list classes]
- When done, send me the annotations/ folder

**Timeline:** Please complete by [date]

See README.txt in the package for detailed instructions.

Questions? Email or call me anytime!

Best,
Aaryn
```

## After Annotation

### Collecting Results

Collaborator sends you back the `annotations/` folder which contains:
- COCO JSON files with their annotations
- Potentially backup files

### Merging Annotations

See `docs/collaborative-annotation-workflow.md` for the complete merging process.

Quick version:
```bash
# Merge all annotation files
make merge-annotations
```

## Troubleshooting

### Chip Extraction Fails
```bash
# Check GCS credentials
gcloud --configuration=asdm auth application-default login

# Verify manifest exists
ls -lh chip-manifest.csv

# Test with small sample
python3 scripts/extract_chips_from_manifest.py --bin aa --count 5 --output-dir test_chips/
```

### Package Too Large
- Reduce chip count: `COUNT=200` instead of 500
- Split into multiple packages by different bins
- Use GCS instead of email/Drive

### Docker Issues on Windows
- Ensure Windows 10/11 Pro, Enterprise, or Education
- WSL2 must be installed and enabled
- At least 8GB RAM, 20GB disk space
- See `cvat/windows-package/README.md` for detailed troubleshooting

## Example: Complete Package Creation

```bash
cd /Users/aaryn/asdm

# Activate environment
source venv/bin/activate

# Run packaging script
./scripts/package_for_collaborator.sh

# Follow prompts:
# Annotator name: kaitlyn
# Bin: aa
# Chip count: 500

# Result: ASDM-Annotation-Package-kaitlyn/ folder ready to share
```

## File Sizes

Typical package sizes:
- 50 chips: ~50 MB
- 200 chips: ~200 MB
- 500 chips: ~500 MB
- 1000 chips: ~1 GB

Plan distribution method accordingly!


