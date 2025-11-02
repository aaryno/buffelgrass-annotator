# CVAT Annotation Setup

CVAT (Computer Vision Annotation Tool) setup for buffelgrass semantic segmentation annotation.

## Quick Start

### Option 1: Complete Automated Setup (Easiest)

Everything in one command - installs CVAT, creates user, creates project, uploads images:

```bash
./cvat/complete-setup.sh \
    --username admin \
    --password yourpassword \
    --email admin@localhost \
    --image-dir ~/asdm-training-data
```

### Option 2: Step-by-Step Setup

```bash
# 1. Install CVAT
./cvat/setup.sh

# 2. Create admin user (bypasses web UI registration)
./cvat/create-user.sh
# Follow prompts to set username/password

# 3. Create project and upload images
python cvat/auto-setup-project.py \
    --username your-username \
    --password your-password \
    --image-dir ~/asdm-training-data
```

### Option 3: Manual Web UI Setup

```bash
# 1. Install CVAT
./cvat/setup.sh

# 2. Open http://localhost:8080 and register first user (becomes admin)

# 3. Either use web UI or automated script for project creation
```

## What is CVAT?

CVAT is an open-source annotation tool developed by Intel/OpenCV that provides:
- **Semantic segmentation** tools (polygons, masks, brushes)
- **SAM integration** for AI-assisted annotation
- **Multi-user** support for team collaboration
- **Multiple export formats** (COCO, YOLO, Pascal VOC, etc.)

## Setup Scripts

Three scripts for different automation levels:

1. **`complete-setup.sh`** - Full automation: installs CVAT, creates user, creates project, uploads images
2. **`setup.sh`** - Installs CVAT only
3. **`create-user.sh`** - Creates admin user via Django (bypasses web registration)
4. **`auto-setup-project.py`** - Creates project with labels and uploads images via API

## Creating Your Buffelgrass Project

### Option 1: Automated Setup (Recommended) 🤖

Use the Python script to automatically create project, labels, task, and upload images:

```bash
# First, create your CVAT account at http://localhost:8080
# Then run the automated setup:

python cvat/auto-setup-project.py \
    --username your-username \
    --password your-password \
    --image-dir ~/asdm-training-data
```

**What it does:**
- ✅ Creates "Buffelgrass Detection" project
- ✅ Adds 8 semantic labels with distinct colors:
  - `buffelgrass` (red) - primary target
  - `soil` (brown)
  - `road` (gray)
  - `building` (purple)
  - `car` (gold)
  - `tree_shrub` (forest green)
  - `cactus` (bright green)
  - `other_grass` (light green)
- ✅ Creates "Tumamoc 2023 Training Set" task
- ✅ Uploads all images from specified directory
- ✅ Returns direct link to start annotating

**Using environment variables:**
```bash
export CVAT_USERNAME=your-username
export CVAT_PASSWORD=your-password
python cvat/auto-setup-project.py --image-dir ~/asdm-training-data
```

**Upload specific images:**
```bash
python cvat/auto-setup-project.py \
    --username admin \
    --password password \
    --images chip1.tif chip2.tif chip3.tif
```

**Create project only (add images later):**
```bash
python cvat/auto-setup-project.py --username admin --password password
```

See `cvat/example-setup.sh` for more examples.

### Option 2: Manual Setup via Web UI

#### 1. Initial Setup
- Open http://localhost:8080
- Create an account (first user = admin)
- Click "Projects" → "Create new project"

#### 2. Project Configuration
```
Name: Buffelgrass Detection
Labels: 
  - buffelgrass (red) - primary invasive species target
  - soil (brown) - bare ground
  - road (gray) - paved/unpaved roads
  - building (purple) - structures
  - car (gold) - vehicles
  - tree_shrub (forest green) - native woody vegetation
  - cactus (bright green) - native cacti (saguaro, prickly pear, etc.)
  - other_grass (light green) - native grasses
```

#### 3. Create Task
- Click "Tasks" → "Create new task"
- Name: "Tumamoc 2023 Training Set"
- Project: Select "Buffelgrass Detection"
- Upload training chips (GeoTIFF or JPEG)

## Annotation Workflow

### Basic Tools
1. **Polygon Tool** - Draw precise boundaries around buffelgrass
2. **Brush Tool** - Paint buffelgrass regions
3. **AI Tools (SAM)** - Click to auto-segment buffelgrass patches

### Recommended Approach
1. Start with a small batch (10-20 images)
2. Use SAM tool for quick initial annotations
3. Refine boundaries with polygon/brush tools
4. Mark difficult cases for review
5. Export and validate annotations

### Keyboard Shortcuts
- `N` - Next frame/image
- `P` - Previous frame/image
- `Ctrl+S` - Save annotations
- `Space` - Play/pause (for video)
- `F` - Toggle fit image to screen

## Exporting Annotations

### For GETI Training
1. Go to your task
2. Click "Actions" → "Export task dataset"
3. Format: **COCO 1.0** (recommended for segmentation)
4. Download ZIP file
5. Extract and convert to GETI format if needed

### Export Formats Available
- **COCO 1.0** - Standard format, widely compatible
- **Datumaro** - Intel's format (direct GETI compatibility)
- **Segmentation mask 1.1** - Raw masks
- **YOLO** - For detection workflows
- **LabelMe** - JSON format

## Uploading Training Data from GCS

### Option 1: Download Locally First
```bash
# Create local directory
mkdir -p ~/asdm-training-data

# Download chips from GCS
gsutil -m cp -r gs://tumamoc-2023/training_chips/*.tif ~/asdm-training-data/

# Upload to CVAT via web UI
```

### Option 2: Use CVAT SDK
```python
from cvat_sdk import make_client

# Connect to local CVAT
client = make_client(
    host="http://localhost:8080",
    credentials=("username", "password")
)

# Create task and upload images
client.tasks.create_from_data(
    project_id=1,
    resources=['~/asdm-training-data/*.tif']
)
```

## Managing CVAT

### Start/Stop
```bash
# Stop (preserves data)
cd ~/cvat && docker compose stop

# Start again
cd ~/cvat && docker compose start

# Restart
cd ~/cvat && docker compose restart

# Shutdown (removes containers, keeps data)
cd ~/cvat && docker compose down

# Full cleanup (⚠️ removes all data)
cd ~/cvat && docker compose down -v
```

### View Logs
```bash
# All services
cd ~/cvat && docker compose logs -f

# Specific service
cd ~/cvat && docker compose logs -f cvat_server
```

### Backup Annotations
```bash
# Backup CVAT database
docker exec cvat_db pg_dump -U root -d cvat > cvat_backup_$(date +%Y%m%d).sql

# Backup uploaded media
docker cp cvat_cvat_server_1:/home/django/data ./cvat_data_backup
```

## Tips for Buffelgrass Annotation

### Label Definitions

**buffelgrass** (Primary Target)
- Invasive grass (*Pennisetum ciliare*)
- Color: Yellowish to brown in dry season, green when active
- Texture: Distinctive tufted/clumped appearance
- Pattern: Often clustered along washes and disturbed areas
- Context: Common near roads, cleared areas, after fires

**soil**
- Bare ground, exposed earth
- No vegetation cover

**road**
- Paved or unpaved roads, trails, paths
- Includes driveways and parking areas

**building**
- Structures, houses, sheds, walls
- Man-made constructions

**car**
- Vehicles of any type
- Cars, trucks, RVs

**tree_shrub**
- Native woody vegetation
- Mesquite, palo verde, ironwood, etc.
- Multi-branched shrubs

**cactus**
- Native cacti species
- Saguaro, prickly pear, cholla, barrel cactus, etc.
- Distinct from other vegetation

**other_grass**
- Native grasses (NOT buffelgrass)
- Bunch grasses, native perennial grasses
- When uncertain if grass is buffelgrass or native

### Annotation Best Practices
1. **Be consistent** - Use same boundaries for similar features
2. **Mark uncertainty** - Use attributes/tags for ambiguous regions
3. **Annotate edges carefully** - Boundaries matter for segmentation
4. **Check different zoom levels** - Catch small patches
5. **Take breaks** - Annotation fatigue leads to errors

### Dealing with Difficult Cases
- **Mixed vegetation**: Annotate dominant species
- **Dead/dormant buffelgrass**: Include if structural features visible
- **Shadows**: Annotate based on visible features
- **Small patches**: Include patches >5 pixels
- **Overlapping vegetation**: Draw approximate boundary

## Integration with GETI

Once you have annotated training data in CVAT:

### Convert COCO to GETI Format
```python
from geti_sdk.annotation_readers import DatumAnnotationReader
from geti_sdk import Geti

# Export from CVAT in COCO format
# Convert using geti_sdk tools
reader = DatumAnnotationReader(annotations_directory="./coco_export")
annotations = reader.read_annotations()

# Upload to GETI project
geti = Geti(host="http://your-geti-instance", username="user", password="pass")
project = geti.get_project("buffelgrass-detection")
project.upload_annotations(annotations)
```

## Troubleshooting

**CVAT won't start:**
- Check Docker is running: `docker info`
- Check port 8080 is free: `lsof -i :8080`
- View logs: `cd ~/cvat && docker compose logs`

**Can't upload images:**
- Check file format (JPEG, PNG, TIFF supported)
- Verify file size (default max: 1GB per task)
- Check CVAT logs for errors

**Performance is slow:**
- Reduce image size/resolution
- Increase Docker memory allocation (Docker Desktop settings)
- Close other applications

**Lost annotations:**
- Check autosave is enabled (Settings → Workspace)
- Check server logs for errors
- Restore from database backup

## Resources

- [CVAT Documentation](https://opencv.github.io/cvat/docs/)
- [CVAT User Guide](https://opencv.github.io/cvat/docs/manual/)
- [CVAT REST API](https://opencv.github.io/cvat/docs/api_sdk/sdk/)

---

*This setup provides a lightweight, production-ready annotation environment for the buffelgrass mapping project.*

