#!/bin/bash
# Quick script to count files in downloaded Dropbox folder
# Usage: ./count_dropbox_files.sh /path/to/dropbox/folder

set -e

FOLDER="${1:-.}"

if [ ! -d "$FOLDER" ]; then
    echo "Error: Directory '$FOLDER' not found"
    echo "Usage: $0 /path/to/dropbox/folder"
    exit 1
fi

echo "Counting files in: $FOLDER"
echo "================================"
echo ""

# Count by file type
echo "By file type:"
find "$FOLDER" -type f -name "*.jpg" -o -name "*.jpeg" | wc -l | xargs printf "  JPEG: %d files\n"
find "$FOLDER" -type f -name "*.jp2" | wc -l | xargs printf "  JPEG2000: %d files\n"
find "$FOLDER" -type f -name "*.tif" -o -name "*.tiff" | wc -l | xargs printf "  TIFF: %d files\n"

echo ""
TOTAL=$(find "$FOLDER" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.jp2" -o -name "*.tif" -o -name "*.tiff" \) | wc -l | xargs)
echo "Total image files: $TOTAL"

# Calculate total size
echo ""
echo "Total size:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    find "$FOLDER" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.jp2" -o -name "*.tif" -o -name "*.tiff" \) -exec stat -f%z {} + | awk '{s+=$1} END {printf "  %.2f GB\n", s/1024/1024/1024}'
else
    # Linux
    find "$FOLDER" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.jp2" -o -name "*.tif" -o -name "*.tiff" \) -exec stat -c%s {} + | awk '{s+=$1} END {printf "  %.2f GB\n", s/1024/1024/1024}'
fi

echo ""
echo "================================"
echo "List of files:"
find "$FOLDER" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.jp2" -o -name "*.tif" -o -name "*.tiff" \) | sort

