#!/bin/bash
set -e

# Simple deployment using existing rasterio image
PROJECT_ID="asdm-399400"
JOB_NAME="cog-converter-simple"
REGION="us-central1"

# Use official rasterio image
IMAGE="ghcr.io/osgeo/gdal:ubuntu-small-latest"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Simple Cloud Run Job - COG Conversion (No Build Needed)   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  Note: This approach processes files sequentially but reliably."
echo "   Each task will convert multiple files."
echo ""
echo "Project: $PROJECT_ID"
echo "Job: $JOB_NAME"
echo ""

# Create a simple conversion script inline
SCRIPT='
#!/bin/bash
apt-get update -qq && apt-get install -y -qq python3-pip
pip3 install -q google-cloud-storage rasterio rio-cogeo

python3 << "PYTHON_END"
import os
from google.cloud import storage
from pathlib import Path
import tempfile
import subprocess

bucket_name = "tumamoc-2023"
source_prefix = "source-jpg/"
cog_prefix = "cogs/"

client = storage.Client()
bucket = client.bucket(bucket_name)

# Get files to process
source_blobs = list(bucket.list_blobs(prefix=source_prefix))
source_files = [b.name for b in source_blobs if not b.name.endswith("/")]

cog_blobs = list(bucket.list_blobs(prefix=cog_prefix))
existing = {Path(b.name).stem for b in cog_blobs}

to_process = [f for f in source_files if Path(f).stem not in existing]

print(f"Found {len(to_process)} files to convert")

for i, src in enumerate(to_process[:10], 1):  # Process 10 per task
    print(f"\n[{i}/10] {Path(src).name}")
    with tempfile.TemporaryDirectory() as tmpdir:
        local_src = f"{tmpdir}/{Path(src).name}"
        local_cog = f"{tmpdir}/{Path(src).stem}.tif"
        
        bucket.blob(src).download_to_filename(local_src)
        
        subprocess.run([
            "rio", "cogeo", "create", local_src, local_cog,
            "--co", "COMPRESS=JPEG", "--co", "TILED=YES"
        ], check=True, capture_output=True)
        
        cog_path = f"{cog_prefix}{Path(src).stem}.tif"
        bucket.blob(cog_path).upload_from_filename(local_cog)
        print(f"  ✓ Uploaded to {cog_path}")
        
print("\n✓ Task complete")
PYTHON_END
'

echo "$SCRIPT" > /tmp/convert_job.sh
chmod +x /tmp/convert_job.sh

# Calculate number of tasks needed
TOTAL_FILES=$(gsutil ls gs://tumamoc-2023/source-jpg/ | wc -l)
COGS_EXIST=$(gsutil ls gs://tumamoc-2023/cogs/ 2>/dev/null | wc -l || echo 0)
FILES_NEEDED=$((TOTAL_FILES - COGS_EXIST))
TASKS=$((FILES_NEEDED / 10 + 1))

if [ $TASKS -gt 100 ]; then
    TASKS=100  # Cap at 100 parallel tasks
fi

echo "Files to convert: $FILES_NEEDED"
echo "Parallel tasks: $TASKS"
echo ""
read -p "Continue? [y/N]: " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Creating Cloud Run Job..."

# Create or update job
gcloud run jobs create "$JOB_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --image="$IMAGE" \
    --tasks="$TASKS" \
    --max-retries=2 \
    --task-timeout=30m \
    --memory=2Gi \
    --cpu=2 \
    --execute-now \
    --command="/bin/bash" \
    --args="-c" \
    --args="$SCRIPT" \
    2>&1 || \
gcloud run jobs update "$JOB_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --image="$IMAGE" \
    --tasks="$TASKS" \
    --max-retries=2 \
    --task-timeout=30m \
    --memory=2Gi \
    --cpu=2 \
    2>&1 && \
gcloud run jobs execute "$JOB_NAME" --project="$PROJECT_ID" --region="$REGION" --wait

echo ""
echo "✓ Job complete!"
echo ""
echo "Check results:"
echo "  make status"


