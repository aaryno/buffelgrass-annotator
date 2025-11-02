#!/bin/bash
set -euo pipefail

# Deploy chip extraction Cloud Run job
#
# Usage:
#   ./deploy_chip_extraction.sh [--tasks N] [--execute]
#
# Options:
#   --tasks N    Number of parallel tasks (default: 50)
#   --execute    Run the job after deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ID="asdm"
REGION="us-central1"
JOB_NAME="chip-extraction"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"
TASKS=50
EXECUTE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tasks)
            TASKS="$2"
            shift 2
            ;;
        --execute)
            EXECUTE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--tasks N] [--execute]"
            exit 1
            ;;
    esac
done

echo "================================================================"
echo "  Chip Extraction Cloud Run Job Deployment"
echo "================================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Job: ${JOB_NAME}"
echo "Parallel tasks: ${TASKS}"
echo ""

# Build container
echo "Building container image..."
cd "${SCRIPT_DIR}"
gcloud --configuration=asdm builds submit \
    --tag "${IMAGE_NAME}" \
    --file chip_extraction.Dockerfile \
    .

echo ""
echo "✓ Container image built: ${IMAGE_NAME}"
echo ""

# Deploy Cloud Run job
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
    --set-env-vars "CHIPS_BUCKET=tumamoc-2023" \
    --set-env-vars "CHIPS_PREFIX=training_chips/1024x1024/" \
    --set-env-vars "CHIPS_PER_IMAGE=4" \
    --set-env-vars "CHIP_SIZE=1024"

echo ""
echo "✓ Cloud Run job deployed"
echo ""

# Execute if requested
if [ "$EXECUTE" = true ]; then
    echo "Executing job..."
    echo ""
    gcloud --configuration=asdm run jobs execute "${JOB_NAME}" \
        --region "${REGION}"
    
    echo ""
    echo "================================================================"
    echo "  Job Execution Started"
    echo "================================================================"
    echo ""
    echo "Monitor progress:"
    echo "  gcloud --configuration=asdm run jobs executions list --job ${JOB_NAME} --region ${REGION}"
    echo ""
    echo "View logs:"
    echo "  gcloud --configuration=asdm logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit 50"
    echo ""
    echo "Expected output:"
    echo "  ~975 COGs × 4 chips = ~3,900 chips"
    echo "  Distributed into 10 folders (01-10)"
    echo "  Location: gs://tumamoc-2023/training_chips/1024x1024/{01-10}/"
    echo ""
else
    echo "================================================================"
    echo "  Deployment Complete (not executed)"
    echo "================================================================"
    echo ""
    echo "To execute the job:"
    echo "  gcloud --configuration=asdm run jobs execute ${JOB_NAME} --region ${REGION}"
    echo ""
    echo "Or re-run with --execute flag:"
    echo "  ./deploy_chip_extraction.sh --execute"
    echo ""
fi


