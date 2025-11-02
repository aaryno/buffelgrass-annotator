#!/bin/bash
# Package CVAT and chips for distribution to annotators

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ASDM Annotation Package Builder                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get annotator name
read -p "Annotator name (e.g., kaitlyn, annotator1): " ANNOTATOR
if [ -z "$ANNOTATOR" ]; then
    echo -e "${RED}❌ Annotator name is required${NC}"
    exit 1
fi

# Get bin to extract
read -p "Manifest bin to extract (e.g., aa, rf, xy): " BIN
if [ -z "$BIN" ]; then
    echo -e "${RED}❌ Bin is required${NC}"
    exit 1
fi

# Get chip count
read -p "Number of chips to extract [500]: " COUNT
COUNT=${COUNT:-500}

# Set output directory
PACKAGE_DIR="ASDM-Annotation-Package-${ANNOTATOR}"

echo ""
echo -e "${GREEN}Creating package for: ${ANNOTATOR}${NC}"
echo -e "  Bin: ${BIN}"
echo -e "  Chips: ${COUNT}"
echo -e "  Output: ${PACKAGE_DIR}/"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Create directory structure
echo ""
echo -e "${BLUE}📁 Creating directory structure...${NC}"
mkdir -p "${PACKAGE_DIR}/cvat-docker"
mkdir -p "${PACKAGE_DIR}/chips"
mkdir -p "${PACKAGE_DIR}/project"

# Copy CVAT files
echo -e "${BLUE}📋 Copying CVAT Docker files...${NC}"
cp cvat/windows-package/start-cvat.bat "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/stop-cvat.bat "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/docker-compose.yml "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/nginx.conf "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/setup-project.py "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/README.md "${PACKAGE_DIR}/cvat-docker/"
cp cvat/windows-package/GCS-SETUP.md "${PACKAGE_DIR}/cvat-docker/"

# Extract chips from manifest
echo -e "${BLUE}✂️  Extracting ${COUNT} chips from bin '${BIN}'...${NC}"
source venv/bin/activate
python3 scripts/extract_chips_from_manifest.py \
    --bin "${BIN}" \
    --count "${COUNT}" \
    --output-dir "${PACKAGE_DIR}/chips/"

# Check if extraction was successful
CHIP_COUNT=$(ls -1 "${PACKAGE_DIR}/chips/" 2>/dev/null | wc -l)
if [ "$CHIP_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No chips extracted. Check errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Extracted ${CHIP_COUNT} chips${NC}"

# Create README for the package
echo -e "${BLUE}📝 Creating package README...${NC}"
cat > "${PACKAGE_DIR}/README.txt" << EOF
ASDM Tumamoc Hill Vegetation Annotation Package
===============================================

Annotator: ${ANNOTATOR}
Bin: ${BIN}
Chips: ${CHIP_COUNT}
Date: $(date +"%Y-%m-%d")

GETTING STARTED
==============

1. Install Docker Desktop for Windows:
   https://docs.docker.com/desktop/setup/install/windows-install/

2. Double-click "cvat-docker/start-cvat.bat" to start CVAT
   (First run takes 10-15 minutes to download images)

3. Open browser to: http://localhost:8080

4. Create an account and start annotating!

DIRECTORY STRUCTURE
==================

cvat-docker/    - CVAT Docker setup files
  start-cvat.bat   - START HERE: Double-click to launch CVAT
  stop-cvat.bat    - Stop CVAT when done
  README.md        - Detailed instructions
  
chips/          - ${CHIP_COUNT} images to annotate

project/        - (empty, will contain shared project config)

annotations/    - (created automatically, your annotations go here)

IMPORTANT NOTES
==============

- Keep all folders in the same location
- Don't rename folders
- Your annotations auto-save to "annotations/" folder
- When done, send Aaryn the "annotations/" folder contents
- See cvat-docker/README.md for detailed instructions

SUPPORT
=======

Questions? Contact:
Aaryn Munoz
aaryno@gmail.com

EOF

# Create a checklist file
cat > "${PACKAGE_DIR}/CHECKLIST.txt" << EOF
ANNOTATION CHECKLIST
===================

□ Installed Docker Desktop for Windows
□ Extracted package to a permanent location (e.g., C:\Users\YourName\ASDM\)
□ Double-clicked cvat-docker/start-cvat.bat
□ Waited for "CVAT is ready" message
□ Opened http://localhost:8080 in browser
□ Created user account
□ Created project (or loaded shared project)
□ Loaded chips from the chips/ folder
□ Annotated all ${CHIP_COUNT} images
□ Exported annotations to annotations/ folder
□ Sent annotations/ folder to Aaryn
□ Celebrated! 🎉

NOTES:
- Start date: __________
- End date: __________
- Issues encountered: ___________________________

EOF

# Calculate package size
PACKAGE_SIZE=$(du -sh "${PACKAGE_DIR}" | awk '{print $1}')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Package Created Successfully!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Location: ${PACKAGE_DIR}/"
echo -e "  Size: ${PACKAGE_SIZE}"
echo -e "  Chips: ${CHIP_COUNT} images"
echo ""

# Offer to create ZIP
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Create ZIP file:"
echo -e "   ${BLUE}zip -r ${PACKAGE_DIR}.zip ${PACKAGE_DIR}/${NC}"
echo ""
echo "2. Share via:"
echo "   • Google Drive"
echo "   • Dropbox"
echo "   • USB drive"
echo "   • Or upload to GCS:"
echo -e "     ${BLUE}gcloud --configuration=asdm storage cp -r ${PACKAGE_DIR}/ gs://tumamoc-2023/annotation-packages/${ANNOTATOR}/${NC}"
echo ""

# Ask if user wants to create ZIP now
read -p "Create ZIP file now? [y/N]: " CREATE_ZIP
if [[ "$CREATE_ZIP" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📦 Creating ZIP file...${NC}"
    zip -r "${PACKAGE_DIR}.zip" "${PACKAGE_DIR}/"
    ZIP_SIZE=$(du -sh "${PACKAGE_DIR}.zip" | awk '{print $1}')
    echo -e "${GREEN}✓ ZIP created: ${PACKAGE_DIR}.zip (${ZIP_SIZE})${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"


