#!/usr/bin/env bash
# Example usage of CVAT setup scripts

set -euo pipefail

echo "🌾 CVAT Buffelgrass Project - Setup Examples"
echo "============================================="
echo ""

# Example 0: Complete one-command setup
echo "Example 0: COMPLETE AUTOMATED SETUP (Recommended)"
echo "--------------------------------------------------"
echo "./cvat/complete-setup.sh \\"
echo "    --username admin \\"
echo "    --password mypassword \\"
echo "    --email admin@localhost \\"
echo "    --image-dir ~/asdm-training-data"
echo ""
echo "This does everything: installs CVAT, creates user, creates project, uploads images"
echo ""
echo ""

# Example 1: Create user only
echo "Example 1: Create admin user"
echo "-----------------------------"
echo "./cvat/create-user.sh"
echo "# Follow prompts for username/password"
echo ""
echo "Or with environment variables:"
echo "export CVAT_USERNAME=admin"
echo "export CVAT_EMAIL=admin@localhost"
echo "export CVAT_PASSWORD=mypassword"
echo "./cvat/create-user.sh"
echo ""
echo ""

# Example 2: Create project only (no images yet)
echo "Example 2: Create project with labels (no images)"
echo "---------------------------------------------------"
echo "python cvat/auto-setup-project.py \\"
echo "    --username admin \\"
echo "    --password yourpassword"
echo ""

# Example 2: Create project and upload from directory
echo "Example 2: Create project and upload images from directory"
echo "-----------------------------------------------------------"
echo "python cvat/auto-setup-project.py \\"
echo "    --username admin \\"
echo "    --password yourpassword \\"
echo "    --image-dir ~/asdm-training-data"
echo ""

# Example 3: Using environment variables
echo "Example 3: Using environment variables for credentials"
echo "--------------------------------------------------------"
echo "export CVAT_USERNAME=admin"
echo "export CVAT_PASSWORD=yourpassword"
echo "python cvat/auto-setup-project.py --image-dir ~/asdm-training-data"
echo ""

# Example 4: Specific images
echo "Example 4: Upload specific images"
echo "----------------------------------"
echo "python cvat/auto-setup-project.py \\"
echo "    --username admin \\"
echo "    --password yourpassword \\"
echo "    --images image1.tif image2.tif image3.tif"
echo ""

# Example 5: Download from GCS first, then upload
echo "Example 5: Download from GCS, then upload to CVAT"
echo "--------------------------------------------------"
echo "# Download training chips from GCS"
echo "mkdir -p ~/asdm-training-data"
echo "gsutil -m cp gs://tumamoc-2023/training_chips/*.tif ~/asdm-training-data/"
echo ""
echo "# Upload to CVAT"
echo "python cvat/auto-setup-project.py \\"
echo "    --username admin \\"
echo "    --password yourpassword \\"
echo "    --image-dir ~/asdm-training-data"
echo ""

