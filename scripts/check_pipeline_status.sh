#!/bin/bash

# Quick status check for data pipeline

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ASDM Buffelgrass Data Pipeline Status            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📥 Dropbox → GCS Transfer (521 files total, 70.5 GB)"
SOURCE_COUNT=$(gsutil ls gs://tumamoc-2023/source-jpg/ 2>&1 | grep -v "Warning" | wc -l | tr -d ' ')
echo "   Source JPEGs uploaded: $SOURCE_COUNT / 521"
PERCENT=$((SOURCE_COUNT * 100 / 521))
echo "   Progress: $PERCENT%"
echo ""

echo "🔄 JPEG → COG Conversion"
COG_COUNT=$(gsutil ls gs://tumamoc-2023/cogs/ 2>&1 | grep -v "Warning" | wc -l | tr -d ' ')
echo "   COGs created: $COG_COUNT / $SOURCE_COUNT (from uploaded files)"
if [ $SOURCE_COUNT -gt 0 ]; then
    COG_PERCENT=$((COG_COUNT * 100 / SOURCE_COUNT))
    echo "   Progress: $COG_PERCENT%"
fi
echo ""

echo "📊 Storage Usage"
SOURCE_SIZE=$(gsutil du -sh gs://tumamoc-2023/source-jpg/ 2>&1 | grep -v "Warning" | awk '{print $1}')
COG_SIZE=$(gsutil du -sh gs://tumamoc-2023/cogs/ 2>&1 | grep -v "Warning" | awk '{print $1}')
echo "   Source JPEGs: $SOURCE_SIZE"
echo "   COGs: $COG_SIZE"
echo ""

echo "📝 Recent Activity"
echo "   Dropbox transfer log:"
tail -3 /tmp/transfer.log 2>&1 | head -3 | sed 's/^/     /'
echo ""
echo "   COG conversion log:"
tail -3 /tmp/cog_conversion.log 2>&1 | head -3 | sed 's/^/     /'
echo ""

echo "Run this script again with: ./scripts/check_pipeline_status.sh"


