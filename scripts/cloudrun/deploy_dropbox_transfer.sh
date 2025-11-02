#!/bin/bash
set -e

# Deploy and run Cloud Run Job for parallel Dropbox → GCS transfer
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-asdm-399400}"
JOB_NAME="dropbox-transfer"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"

# Number of parallel tasks
PARALLELISM="${1:-50}"

# Verify Dropbox token secret exists
echo "🔐 Verifying Dropbox token secret..."
if ! gcloud secrets describe dropbox-token --project="${PROJECT_ID}" &>/dev/null; then
    echo "❌ Error: dropbox-token secret not found in Secret Manager"
    echo "   Create it with: cat .dropbox-token | gcloud secrets create dropbox-token --data-file=- --project=${PROJECT_ID}"
    exit 1
fi
echo "   ✓ Secret found"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Cloud Run Jobs - Parallel Dropbox Transfer             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Job: ${JOB_NAME}"
echo "Parallel tasks: ${PARALLELISM}"
echo ""

# Step 1: Build container
echo "📦 Building container image..."
cd dropbox
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_NAME}" \
    .
cd ..

echo ""
echo "✓ Container built: ${IMAGE_NAME}"
echo ""

# Step 2: Create or update job
echo "🚀 Deploying Cloud Run Job..."
if gcloud run jobs describe "${JOB_NAME}" --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "Updating existing job..."
    gcloud run jobs update "${JOB_NAME}" \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_NAME}" \
        --tasks="${PARALLELISM}" \
        --max-retries=2 \
        --task-timeout=30m \
        --memory=512Mi \
        --cpu=1 \
        --set-env-vars="GCS_BUCKET=tumamoc-2023,GCS_PREFIX=source-jpg/" \
        --set-secrets="DROPBOX_TOKEN=dropbox-token:latest"
else
    echo "Creating new job..."
    gcloud run jobs create "${JOB_NAME}" \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${IMAGE_NAME}" \
        --tasks="${PARALLELISM}" \
        --max-retries=2 \
        --task-timeout=30m \
        --memory=512Mi \
        --cpu=1 \
        --set-env-vars="GCS_BUCKET=tumamoc-2023,GCS_PREFIX=source-jpg/" \
        --set-secrets="DROPBOX_TOKEN=dropbox-token:latest"
fi

echo ""
echo "✓ Job deployed"
echo ""

# Step 3: Run the job
echo "▶️  Executing job (${PARALLELISM} parallel workers)..."
echo ""
gcloud run jobs execute "${JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --wait

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       Job Complete!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Check results:"
echo "  gsutil ls gs://tumamoc-2023/source-jpg/ | wc -l"
echo "  gsutil du -sh gs://tumamoc-2023/source-jpg/"
echo ""
echo "View logs:"
echo "  gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit=100 --project=${PROJECT_ID}"

