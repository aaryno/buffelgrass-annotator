#!/bin/bash
set -e

# Deploy and run Cloud Run Job for parallel COG conversion
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-asdm-399400}"
JOB_NAME="cog-converter"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"

# Number of parallel tasks (adjust based on files to process)
PARALLELISM="${1:-50}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Cloud Run Jobs - Parallel COG Conversion             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT_ID"
echo "Job: $JOB_NAME"
echo "Parallel tasks: $PARALLELISM"
echo ""

# Step 1: Build container
echo "📦 Building container image..."
cd "$(dirname "$0")"
gcloud builds submit \
    --project="$PROJECT_ID" \
    --tag="$IMAGE_NAME" \
    .

echo ""
echo "✓ Container built: $IMAGE_NAME"
echo ""

# Step 2: Create or update job
echo "🚀 Deploying Cloud Run Job..."
if gcloud run jobs describe "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "Updating existing job..."
    gcloud run jobs update "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --image="$IMAGE_NAME" \
        --tasks="$PARALLELISM" \
        --max-retries=2 \
        --task-timeout=30m \
        --memory=2Gi \
        --cpu=2
else
    echo "Creating new job..."
    gcloud run jobs create "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --image="$IMAGE_NAME" \
        --tasks="$PARALLELISM" \
        --max-retries=2 \
        --task-timeout=30m \
        --memory=2Gi \
        --cpu=2
fi

echo ""
echo "✓ Job deployed"
echo ""

# Step 3: Run the job
echo "▶️  Executing job (this will process files in parallel)..."
echo ""
gcloud run jobs execute "$JOB_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --wait

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       Job Complete!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Check results:"
echo "  gsutil ls gs://tumamoc-2023/cogs/ | wc -l"
echo "  gsutil du -sh gs://tumamoc-2023/cogs/"
echo ""
echo "View logs:"
echo "  gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit=100 --project=${PROJECT_ID}"

