# Collaborative Annotation Workflow

Complete workflow for parallel buffelgrass annotation using CVAT on Windows.

---

## 🎯 Overview

**Goal:** Annotate 977 training chips using 2+ people working in parallel

**Tools:**
- CVAT (local installation on each computer)
- Windows Docker Desktop
- Python scripts for splitting/merging

**Timeline:** 2-4 weeks depending on team size and hours per week

---

## 📋 Complete Workflow

### Phase 1: Setup (One-time, ~1 hour)

#### For Project Coordinator:

**1. Generate training chips** (if not already done)
```bash
cd ~/asdm
make test-chips  # Test first
make extract-chips  # Generate full set
```

**2. Split dataset for parallel annotation**
```bash
# Split into 2 groups (you + 1 collaborator)
python scripts/split_dataset_by_region.py data/training_chips -n 2

# Output:
# data/chips_split/person_1/  (you)
# data/chips_split/person_2/  (collaborator)
```

**3. Share data with collaborator**
- Copy `person_2` folder to USB drive or Dropbox
- Share `docs/cvat-windows-setup.md` guide
- Provide contact info for questions

#### For Each Annotator:

**1. Follow Windows setup guide**
- See: `docs/cvat-windows-setup.md`
- Install Docker Desktop + CVAT
- ~30 minutes

**2. Import your image set**
- Create CVAT project
- Create task with your assigned images
- Start annotating!

---

### Phase 2: Annotation (2-4 weeks)

#### Daily Workflow (Each Annotator):

```bash
# Start CVAT
cd C:\Users\YourUsername\Documents\cvat
docker compose up -d

# Open browser: http://localhost:8080
# Annotate 25-50 images
# Save frequently (Ctrl+S)

# When done for the day
docker compose stop
```

#### Progress Tracking:
- **Goal:** 25-50 chips per session
- **Frequency:** 3-5 sessions per week
- **Total time:** ~20-40 hours per person

#### Communication:
- Weekly check-ins to compare progress
- Share example annotations for consistency
- Discuss edge cases and ambiguous situations

---

### Phase 3: Export & Merge (1 hour)

#### Each Annotator:

**1. Export annotations from CVAT**
```
Tasks → Your Task → ⋮ → Export task dataset
Format: COCO 1.0
```

**2. Send to coordinator**
- Email or Dropbox the exported `.zip` file
- Include your name in filename: `buffelgrass_person1.zip`

#### Project Coordinator:

**1. Collect all exported files**
```bash
mkdir -p data/annotation_exports
# Place all exported files here:
# - buffelgrass_person1.zip
# - buffelgrass_person2.zip
```

**2. Extract annotation JSON files**
```bash
cd data/annotation_exports
unzip buffelgrass_person1.zip -d person1
unzip buffelgrass_person2.zip -d person2

# Find the annotations.json file in each
mv person1/annotations/instances_default.json person1_annotations.json
mv person2/annotations/instances_default.json person2_annotations.json
```

**3. Merge annotations**
```bash
cd ~/asdm
python scripts/merge_coco_annotations.py \
  data/annotation_exports/person1_annotations.json \
  data/annotation_exports/person2_annotations.json \
  -o data/merged_buffelgrass_annotations.json \
  --verify
```

**Output:**
```
✅ Merge Complete!
Total images:      977
Total annotations: 2,543  (example)
Output file:       data/merged_buffelgrass_annotations.json
```

---

### Phase 4: Training (Next step)

**Import to GETI:**
```python
from geti_sdk import Geti
from geti_sdk.rest_clients import ProjectClient

# Connect to GETI (local or cloud)
geti = Geti(host="http://localhost:8080", token="your_token")

# Import COCO annotations
project_client = ProjectClient(...)
project_client.import_coco_dataset(
    "data/merged_buffelgrass_annotations.json",
    project_name="Buffelgrass Segmentation"
)

# Start training!
```

---

## 📊 Effort Breakdown

### Per Annotator (Example: 500 chips each)

| Task | Time | Notes |
|------|------|-------|
| Setup | 30 min | One-time |
| Learning CVAT | 30 min | First session |
| Annotation | 30-40 hours | 500 chips × 3-5 min each |
| Export | 5 min | Final step |
| **Total** | **~31-41 hours** | Over 2-4 weeks |

### Project Coordinator (Additional)

| Task | Time |
|------|------|
| Generate chips | 30 min |
| Split dataset | 5 min |
| Merge annotations | 5 min |
| **Total** | **~40 min** |

---

## 🎨 Annotation Guidelines

### Buffelgrass Identification

**Include:**
- ✅ Visible buffelgrass clumps
- ✅ Partial clumps at image edges
- ✅ Dead/dried buffelgrass (still visible)

**Exclude:**
- ❌ Native grasses (different texture/color)
- ❌ Shadows without visible grass
- ❌ Ambiguous vegetation (when unsure, skip)

### Annotation Quality Tips

1. **Polygon precision:**
   - Follow grass edges closely
   - Don't include too much background
   - Separate individual clumps

2. **Consistency:**
   - Use same criteria throughout
   - Compare with example annotations
   - Ask if uncertain

3. **Speed vs. Quality:**
   - Quality > Quantity
   - Take breaks every 30-45 min
   - Don't rush through images

---

## 🔧 Troubleshooting

### "My images look different from collaborator's"

**Cause:** Different regions have different lighting/terrain.

**Solution:** This is expected! Just annotate consistently within your set.

### "I found an image with no buffelgrass"

**Solution:** Skip it (press F for next). Empty images are fine.

### "I accidentally annotated wrong class"

**Solution:**
1. Click the polygon
2. Press Delete key
3. Re-annotate correctly
4. Save (Ctrl+S)

### "CVAT is running slow"

**Solutions:**
1. Close other programs
2. Reduce image quality to 75% (Task settings)
3. Work in smaller batches (50 images per task)
4. Restart Docker: `docker compose restart`

---

## 📧 Communication Template

### For Collaborators

**Subject:** Buffelgrass Annotation Project - Getting Started

Hi [Name],

Thanks for helping with the buffelgrass annotation project! Here's everything you need:

**Your dataset:** [Link to person_2 folder]
- Images: 488 chips
- Size: ~50 MB

**Setup guide:** docs/cvat-windows-setup.md
- Estimated setup time: 30 minutes
- Let me know if you hit any issues!

**Target:** 25-50 images per session, 3-5 sessions/week
**Deadline:** [Date] (flexible)

**Questions?** Email/call me anytime.

Thanks!
[Your name]

---

## ✅ Quality Control

### Spot Check (Recommended)

After first 50 annotations from each person:

1. **Review samples** from each annotator
2. **Compare consistency** (polygon precision, inclusion criteria)
3. **Provide feedback** if needed
4. **Adjust guidelines** if ambiguities found

### Final Review

Before training:

```bash
# Count annotations per person
python -c "
import json
with open('data/merged_buffelgrass_annotations.json') as f:
    data = json.load(f)
print(f'Total images: {len(data[\"images\"])}')
print(f'Total annotations: {len(data[\"annotations\"])}')
print(f'Avg per image: {len(data[\"annotations\"])/len(data[\"images\"]):.1f}')
"
```

---

## 🎯 Success Criteria

- ✅ All 977 chips annotated
- ✅ Consistent annotation quality between annotators
- ✅ Successful merge with no duplicate images
- ✅ COCO file imports to GETI without errors
- ✅ Model trains with reasonable accuracy

---

## 📚 Additional Resources

### CVAT Documentation
- Official docs: https://opencv.github.io/cvat/docs/
- Video tutorials: Search "CVAT polygon annotation tutorial"

### COCO Format
- Specification: https://cocodataset.org/#format-data

### GETI SDK
- Documentation: https://github.com/openvinotoolkit/geti-sdk

---

**Questions?** Contact: [Your email/phone]

**Good luck annotating!** 🌿



