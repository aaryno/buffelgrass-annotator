#!/bin/bash
set -euo pipefail

# Deploy chip manifest generation Cloud Run job
#
# Generates CSV manifest of all possible chip windows (30 per COG)
# for ~976 COGs = ~29,280 total chip windows

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ID="asdm-399400"
REGION="us-central1"
JOB_NAME="chip-manifest"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"
TASKS="${1:-50}"  # Default 50 parallel tasks

echo "================================================================"
echo "  Chip Manifest Generation - Cloud Run Job"
echo "================================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Job: ${JOB_NAME}"
echo "Tasks: ${TASKS}"
echo ""

# Build container
echo "Building container image..."
cd "${SCRIPT_DIR}"

# Create temporary build directory with Dockerfile renamed
BUILD_DIR=$(mktemp -d)
cp chip_manifest.Dockerfile "${BUILD_DIR}/Dockerfile"
cp chip_manifest_job.py "${BUILD_DIR}/"

cd "${BUILD_DIR}"
gcloud --configuration=asdm builds submit \
    --project="${PROJECT_ID}" \
    --tag "${IMAGE_NAME}" \
    .

# Cleanup
rm -rf "${BUILD_DIR}"
cd "${SCRIPT_DIR}"

echo ""
echo "✓ Container built"
echo ""

# Deploy job
echo "Deploying Cloud Run job..."
gcloud --configuration=asdm run jobs deploy "${JOB_NAME}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --tasks "${TASKS}" \
    --parallelism "${TASKS}" \
    --max-retries 2 \
    --task-timeout 30m \
    --memory 4Gi \
    --cpu 2 \
    --set-env-vars "SOURCE_BUCKET=tumamoc-2023" \
    --set-env-vars "SOURCE_PREFIX=cogs/" \
    --set-env-vars "OUTPUT_BUCKET=tumamoc-2023"

echo ""
echo "✓ Job deployed"
echo ""

# Execute job
echo "Executing job..."
gcloud --configuration=asdm run jobs execute "${JOB_NAME}" \
    --region "${REGION}"

echo ""
echo "================================================================"
echo "  Job Started"
echo "================================================================"
echo ""
echo "Monitor:"
echo "  gcloud --configuration=asdm run jobs executions list --job ${JOB_NAME} --region ${REGION}"
echo ""
echo "View logs:"
echo "  gcloud --configuration=asdm logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit 50"
echo ""
echo "After completion, merge partial CSVs:"
echo "  ./merge_chip_manifest.sh"
echo ""
echo "Expected output:"
echo "  ~976 COGs × 30 chips = ~29,280 chip windows"
echo "  Location: gs://tumamoc-2023/chip_manifests/partial/task_*.csv"
echo ""

