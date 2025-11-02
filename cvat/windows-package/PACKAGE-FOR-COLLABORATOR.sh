#!/usr/bin/env bash
# Create Windows package for collaborators
# Run this on Mac to create a zip file for Windows users

set -euo pipefail

PACKAGE_NAME="cvat-buffelgrass-windows"
OUTPUT_DIR="./cvat/windows-package-dist"

echo "📦 Creating Windows Package for Collaborators"
echo "=============================================="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create package directory
PKG_DIR="$OUTPUT_DIR/$PACKAGE_NAME"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/data/training_chips"

echo "📋 Copying files..."

# Copy core files
cp ./cvat/windows-package/*.bat "$PKG_DIR/"
cp ./cvat/windows-package/docker-compose.yml "$PKG_DIR/"
cp ./cvat/windows-package/README-WINDOWS.txt "$PKG_DIR/"

# Create sample chips directory with a readme
cat > "$PKG_DIR/data/training_chips/README.txt" << 'EOF'
Place your training chip images (PNG or JPEG) in this directory.

The CVAT server will automatically see these files and you can
import them into your annotation tasks.

For example:
  - chip_001.png
  - chip_002.png
  - ...

After adding files, you can access them in CVAT:
  1. Create a Task
  2. Select files → "Connected file share"
  3. Select your images
  4. Start annotating!
EOF

# Optionally copy some sample chips if they exist
if [ -d "./data/training_chips" ]; then
    echo "📸 Found training chips - copying sample..."
    # Copy first 5 chips as examples
    find ./data/training_chips -name "*.png" -type f | head -5 | while read chip; do
        cp "$chip" "$PKG_DIR/data/training_chips/"
    done
fi

# Create instructions file
cat > "$PKG_DIR/INSTALLATION-INSTRUCTIONS.txt" << 'EOF'
=======================================================================
  CVAT Buffelgrass Annotation - Installation Instructions
=======================================================================

STEP 1: Install Docker Desktop
-------------------------------
1. Download Docker Desktop for Windows:
   https://www.docker.com/products/docker-desktop

2. Run the installer

3. Start Docker Desktop (wait for "Docker Desktop is running" message)

4. (Optional) Create a Docker Hub account if prompted


STEP 2: Extract This Package
-----------------------------
1. Extract this ZIP file to a permanent location, such as:
   C:\Users\YourName\Documents\cvat-buffelgrass\

2. DO NOT use a temporary folder (like Downloads)


STEP 3: Add Your Training Chips
--------------------------------
1. Navigate to the extracted folder

2. Open: data\training_chips\

3. Copy your assigned PNG training images into this folder


STEP 4: Start CVAT
-------------------
1. Make sure Docker Desktop is running

2. Double-click: START-CVAT.bat

3. Wait 2-3 minutes for first-time setup
   (downloads ~3GB of Docker images)

4. Browser will open automatically to http://localhost:8080


STEP 5: Login and Create Project
---------------------------------
Login credentials:
  Username: annotator
  Password: buffelgrass2024

Then create your project:
1. Click "Projects" → "Create new project"
2. Add 8 labels: buffelgrass, soil, road, building, car, 
   tree_shrub, cactus, other_grass
3. Create a task and import your images
4. Start annotating!


TROUBLESHOOTING:
----------------
- If START-CVAT.bat shows "Docker not running":
  → Start Docker Desktop first

- If browser doesn't open automatically:
  → Manually go to http://localhost:8080

- If images don't appear:
  → Make sure they're in data\training_chips\
  → Restart: STOP-CVAT.bat then START-CVAT.bat


For more help, see: README-WINDOWS.txt

=======================================================================
EOF

# Create zip file
echo "🗜️  Creating ZIP archive..."
cd "$OUTPUT_DIR"
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME" > /dev/null

echo ""
echo "✅ Package created successfully!"
echo ""
echo "📦 Package location:"
echo "   $(pwd)/${PACKAGE_NAME}.zip"
echo ""
echo "📤 Send this file to your Windows collaborators"
echo ""
echo "📋 They should:"
echo "   1. Install Docker Desktop for Windows"
echo "   2. Extract the ZIP file"
echo "   3. Add their training chips to data/training_chips/"
echo "   4. Double-click START-CVAT.bat"
echo "   5. Login and start annotating"
echo ""
echo "💾 Package size:"
ls -lh "${PACKAGE_NAME}.zip" | awk '{print "   " $5}'
echo ""

