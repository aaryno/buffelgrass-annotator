# Deployment Guide for Project Coordinator

## Distributing to Annotators

### Step 1: Prepare Package for Each Annotator

For each annotator (e.g., Kaitlyn, annotator2, annotator3, annotator4):

1. **Create a copy of this package**:
   ```bash
   cp -r cvat-windows-package/ buffelgrass-annotation-kaitlyn/
   cd buffelgrass-annotation-kaitlyn/
   ```

2. **Add their assigned chips**:
   ```bash
   # Copy their training chips into chips/ folder
   cp path/to/chips_split/person_1/* ./chips/
   
   # Verify chip count
   ls -1 chips/*.tif | wc -l
   ```

3. **Create a README with their info**:
   ```bash
   cat > ANNOTATOR_INFO.txt << EOF
   Annotator: Kaitlyn
   Assigned chips: 244 images (chips_001 through chips_244)
   Target: 25-50 images per session, 3-5 sessions/week
   Estimated time: ~12-20 hours total
   Coordinator: [Your name]
   Email: [Your email]
   Phone: [Your phone]
   EOF
   ```

4. **Package for distribution**:
   ```bash
   # Create ZIP for transfer
   cd ..
   zip -r buffelgrass-annotation-kaitlyn.zip buffelgrass-annotation-kaitlyn/
   
   # Or copy to USB drive
   cp -r buffelgrass-annotation-kaitlyn/ /Volumes/USB_DRIVE/
   ```

### Step 2: Distribution Methods

**Option A: USB Drive** (Recommended for large datasets)
- Copy entire folder to USB drive
- Hand deliver to each annotator
- Fastest for 1+ GB of training chips

**Option B: Dropbox/Google Drive**
- Upload ZIP file
- Share link with annotator
- Good for remote collaborators

**Option C: Network Share**
- Place on shared network drive
- Provide annotators with path
- Good for on-site team

### Step 3: Annotator Instructions

Send each annotator:

1. **Welcome email** (template below)
2. **Package** (USB/download link)
3. **Installation guide** (README.md included in package)
4. **Your contact info** for questions

#### Email Template

```
Subject: Buffelgrass Annotation Project - Your Training Dataset

Hi [Annotator Name],

Thanks for helping with the buffelgrass mapping project! I've prepared 
everything you need to get started.

WHAT YOU'LL BE ANNOTATING:
- Your dataset: [244] training chip images
- Focus: Identify and outline buffelgrass in aerial imagery
- Estimated time: 12-20 hours total (flexible schedule)
- Target pace: 25-50 images per session, 3-5 times per week

WHAT YOU RECEIVED:
[✓] USB drive with complete annotation package
    (or: Link to download: [Dropbox/Drive link])

GETTING STARTED:
1. Install Docker Desktop (link in README)
2. Extract the package to your Documents folder
3. Double-click "start-cvat.bat" to launch
4. Follow the README for first-time setup (5 minutes)
5. Run: python setup-project.py --username [yourname]
6. Start annotating at http://localhost:8080

IMPORTANT:
- Your annotations save automatically in the "project/" folder
- Back this folder up weekly!
- When complete, export as COCO 1.0 format
- Send the exported ZIP file back to me

QUESTIONS?
- Email: [your email]
- Phone: [your phone]
- I'm available [days/times] for help

DEADLINE:
Flexible! Aim for [date], but let me know if you need more time.

Thank you for contributing to this important conservation work! 🌵

Best,
[Your Name]
Arizona Sonoran Desert Museum
```

## Merging Annotations

### Step 1: Collect Exports

When annotators finish, they'll send you files like:
- `buffelgrass_annotations_kaitlyn.zip`
- `buffelgrass_annotations_person2.zip`
- `buffelgrass_annotations_person3.zip`
- `buffelgrass_annotations_person4.zip`

### Step 2: Extract Annotations

```bash
cd ~/asdm
mkdir -p data/annotation_exports

# Extract each export
cd data/annotation_exports
unzip buffelgrass_annotations_kaitlyn.zip -d kaitlyn
unzip buffelgrass_annotations_person2.zip -d person2
unzip buffelgrass_annotations_person3.zip -d person3
unzip buffelgrass_annotations_person4.zip -d person4

# COCO annotations are typically at:
# kaitlyn/annotations/instances_default.json
# Copy to root for easier merging
cp kaitlyn/annotations/instances_default.json kaitlyn_annotations.json
cp person2/annotations/instances_default.json person2_annotations.json
cp person3/annotations/instances_default.json person3_annotations.json
cp person4/annotations/instances_default.json person4_annotations.json
```

### Step 3: Merge Using Existing Script

```bash
cd ~/asdm

# Merge all annotations
python scripts/merge_coco_annotations.py \
  data/annotation_exports/kaitlyn_annotations.json \
  data/annotation_exports/person2_annotations.json \
  data/annotation_exports/person3_annotations.json \
  data/annotation_exports/person4_annotations.json \
  -o data/merged_buffelgrass_annotations.json \
  --verify

# Verify output
python -c "
import json
with open('data/merged_buffelgrass_annotations.json') as f:
    data = json.load(f)
print(f'✅ Total images: {len(data[\"images\"])}')
print(f'✅ Total annotations: {len(data[\"annotations\"])}')
print(f'✅ Avg per image: {len(data[\"annotations\"])/len(data[\"images\"]):.1f}')
"
```

### Step 4: Upload to GCS

```bash
# Upload merged annotations
gcloud --configuration=asdm storage cp \
  data/merged_buffelgrass_annotations.json \
  gs://tumamoc-2023/training_annotations/

# Upload individual exports as backups
gcloud --configuration=asdm storage cp \
  data/annotation_exports/*.json \
  gs://tumamoc-2023/training_annotations/individual/
```

## Quality Control

### Spot Check After First 50 Annotations

```python
# Check annotation quality from first batch
import json

# Load annotator's export
with open('data/annotation_exports/kaitlyn_annotations.json') as f:
    data = json.load(f)

# Basic stats
num_images = len(data['images'])
num_annotations = len(data['annotations'])

print(f"Images annotated: {num_images}")
print(f"Total annotations: {num_annotations}")
print(f"Avg per image: {num_annotations/num_images:.1f}")

# Check if all images have at least one annotation
image_ids_with_annotations = set(a['image_id'] for a in data['annotations'])
image_ids = set(img['id'] for img in data['images'])
images_without_annotations = image_ids - image_ids_with_annotations

if images_without_annotations:
    print(f"⚠️  {len(images_without_annotations)} images have no annotations")
    print("   (This is OK if images contain no buffelgrass)")
else:
    print("✅ All images have annotations")
```

### Review Sample Annotations in CVAT

1. Import annotator's export into your CVAT instance
2. Review 10-20 random annotations
3. Check for:
   - Consistent labeling of buffelgrass
   - Appropriate boundary precision
   - Correct use of labels
4. Provide feedback if needed

## Troubleshooting Annotator Issues

### "Can't install Docker Desktop - not admin"

**Solution**: Work with IT or have them use different machine where they have admin rights.

### "CVAT is slow"

**Solutions**:
1. Reduce image quality in CVAT settings (75%)
2. Increase Docker Desktop memory allocation (Settings → Resources → Memory: 8GB)
3. Close other applications
4. Work with smaller batches (split task into multiple smaller tasks)

### "Lost all my annotations!"

**Recovery**:
1. Check `project/db` folder - should contain PostgreSQL database
2. If database exists:
   ```bash
   # Restart CVAT
   stop-cvat.bat
   start-cvat.bat
   ```
3. If database lost, check if they have backups or recent exports

**Prevention**: Emphasize backing up `project/` folder weekly!

### "Export failed"

**Solutions**:
1. Try exporting smaller batches
2. Check disk space (exports can be large)
3. Try different format (COCO 1.0 vs Datumaro)
4. Export via API if web UI fails:
   ```python
   from cvat_sdk import make_client
   client = make_client(host="http://localhost:8080", credentials=("user", "pass"))
   task = client.tasks.retrieve(TASK_ID)
   task.export_dataset("COCO 1.0", "annotations.zip")
   ```

## Coordinator Checklist

### Before Distribution
- [ ] Split training chips into balanced sets
- [ ] Test package on Windows machine
- [ ] Prepare USB drives or upload to cloud storage
- [ ] Create annotator assignment list
- [ ] Draft welcome email
- [ ] Schedule kickoff meeting/call

### During Annotation
- [ ] Week 1: Check in with all annotators (are they set up?)
- [ ] Week 2: Request sample export from each (quality check)
- [ ] Provide feedback on annotation quality
- [ ] Weekly progress check-ins
- [ ] Answer questions promptly

### After Collection
- [ ] Receive all exports
- [ ] Verify no missing chips
- [ ] Merge annotations
- [ ] Upload to GCS
- [ ] Thank annotators!
- [ ] Proceed to model training

## Next Steps: Model Training

After merging, proceed with GETI training:

```python
from geti_sdk import Geti

geti = Geti(host="http://localhost:8080", token="your_token")

# Import merged COCO dataset
project = geti.create_project(
    project_name="Buffelgrass Segmentation",
    project_type="segmentation"
)

project.upload_coco_dataset("data/merged_buffelgrass_annotations.json")

# Start training
project.train_task()
```

See `docs/remote-training-via-sdk.md` for complete training workflow.

---

**Questions?** Update this guide as you discover better practices!


