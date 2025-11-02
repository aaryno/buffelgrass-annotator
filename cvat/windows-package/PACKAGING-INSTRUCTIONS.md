# Packaging Instructions for CVAT Windows Distribution

## What to Package

The collaborator needs:
1. The CVAT Docker configuration files
2. The shared project configuration
3. Initial chip images to annotate

## Step 1: Prepare the Package

Create a folder structure like this:
```
ASDM-Annotation-Package/
├── cvat-docker/              (the Windows package)
│   ├── start-cvat.bat
│   ├── stop-cvat.bat
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── setup-project.py
│   ├── README.md
│   └── GCS-SETUP.md
├── chips/                     (sample chips to annotate)
│   ├── chip001.png
│   ├── chip002.png
│   └── ...
└── project/                   (shared project config)
    └── tumamoc-classes.json
```

## Step 2: Export the Project Configuration

After you've created the CVAT project with all your classes:

1. Open CVAT in your browser (http://localhost:8080)
2. Go to Projects → Your Project
3. Click the "⋮" menu → Export project dataset
4. Select format: "CVAT 1.1"
5. Save as `tumamoc-classes.json`
6. Place in the `project/` folder

## Step 3: Select and Extract Chips

Based on your chip manifest, select chips for this annotator:

```bash
# Example: Extract 500 chips from bin 'aa' for annotator 1
cd /Users/aaryn/asdm
source venv/bin/activate

# Create a script to extract chips from the manifest
# This will read the manifest and extract the actual chip images from COGs
# (You'll need to implement this extraction script)
```

## Step 4: Package Everything

### Option A: ZIP File (Simple)

```bash
cd /Users/aaryn/asdm
mkdir -p ASDM-Annotation-Package/cvat-docker
mkdir -p ASDM-Annotation-Package/chips
mkdir -p ASDM-Annotation-Package/project

# Copy CVAT files
cp cvat/windows-package/* ASDM-Annotation-Package/cvat-docker/

# Copy chips (after extraction)
cp /path/to/extracted/chips/* ASDM-Annotation-Package/chips/

# Copy project config (after export)
cp /path/to/tumamoc-classes.json ASDM-Annotation-Package/project/

# Create ZIP
zip -r ASDM-Annotation-Package.zip ASDM-Annotation-Package/
```

### Option B: Cloud Storage (Better for large datasets)

```bash
# Upload to Google Cloud Storage
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
gcloud --configuration=asdm storage cp -r ASDM-Annotation-Package/ gs://tumamoc-2023/annotation-packages/annotator1/

# Generate a signed URL (valid for 7 days)
gcloud --configuration=asdm storage sign-url gs://tumamoc-2023/annotation-packages/annotator1/ASDM-Annotation-Package.zip --duration=7d
```

## Step 5: Send to Collaborator

### Email Template

```
Subject: ASDM Image Annotation - Setup Package

Hi [Name],

Please find the annotation package for the Tumamoc Hill vegetation mapping project.

**Download Link:** [insert link or attachment]

**Setup Instructions:**

1. Install Docker Desktop for Windows:
   https://docs.docker.com/desktop/setup/install/windows-install/

2. Extract the package to a location like:
   C:\Users\[YourName]\ASDM-Annotation\

3. Double-click `cvat-docker\start-cvat.bat` to start CVAT
   (First run will take 10-15 minutes to download Docker images)

4. Open your browser to: http://localhost:8080

5. Create an account and start annotating!

**Important Notes:**
- Keep the `chips/` folder in the same location
- Your annotations will be saved in the `annotations/` folder
- When done, send me the `annotations/` folder contents
- See the README.md file for detailed instructions

Let me know if you have any issues!

Best,
Aaryn
```

## Step 6: After Annotation is Complete

Collaborator sends you back:
- The `annotations/` folder (contains COCO JSON exports)

You merge their annotations with yours using the merge workflow documented in `docs/collaborative-annotation-workflow.md`.

## Notes

- **Chip images**: Plan to extract 500-1000 chips per annotator
- **File size**: Expect ~500MB-2GB per package depending on chip count
- **Distribution**: Consider using Google Drive, Dropbox, or GCS for large packages
- **Security**: Use signed URLs with expiration for GCS sharing


