#!/bin/bash
#
# Manual Dropbox to GCS transfer (no API needed)
# Run this in Cloud Shell
#
# Usage:
# 1. Edit DROPBOX_FILES array below with your file URLs
# 2. Upload this script to Cloud Shell
# 3. Run: ./dropbox_to_gcs_manual.sh

set -e

GCS_BUCKET="gs://tumamoc-2023/raw_jpegs"

# Add your Dropbox file direct download URLs here
# To get direct download link: Change ?dl=0 to ?dl=1 in Dropbox URL
DROPBOX_FILES=(
    # Example format:
    # "https://www.dropbox.com/scl/fi/[id]/file1.jpg?rlkey=[key]&dl=1"
    # "https://www.dropbox.com/scl/fi/[id]/file2.jpg?rlkey=[key]&dl=1"
    
    # Paste your file URLs below:
    
)

echo "========================================"
echo "Dropbox → GCS Transfer"
echo "========================================"
echo "Destination: $GCS_BUCKET"
echo "Total files: ${#DROPBOX_FILES[@]}"
echo ""

if [ ${#DROPBOX_FILES[@]} -eq 0 ]; then
    echo "❌ No files configured!"
    echo ""
    echo "Edit this script and add Dropbox file URLs to DROPBOX_FILES array"
    echo ""
    echo "Steps to get file URLs:"
    echo "1. Open Dropbox shared folder in browser"
    echo "2. For each file, right-click → 'Copy link'"
    echo "3. Change ?dl=0 to ?dl=1 at end of URL"
    echo "4. Add to DROPBOX_FILES array above"
    exit 1
fi

SUCCESS=0
FAILED=0

for i in "${!DROPBOX_FILES[@]}"; do
    NUM=$((i + 1))
    TOTAL=${#DROPBOX_FILES[@]}
    URL="${DROPBOX_FILES[$i]}"
    
    # Extract filename from URL
    FILENAME=$(basename "$URL" | cut -d'?' -f1)
    
    echo "[$NUM/$TOTAL] $FILENAME"
    
    # Download and pipe to GCS
    if wget -q --show-progress -O - "$URL" | gsutil -q cp - "${GCS_BUCKET}/${FILENAME}"; then
        echo "  ✓ Complete: ${GCS_BUCKET}/${FILENAME}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  ✗ Failed"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "========================================"
echo "Transfer Complete"
echo "========================================"
echo "Successful: $SUCCESS"
echo "Failed: $FAILED"
echo ""
echo "Files available at: $GCS_BUCKET"
echo "========================================"

