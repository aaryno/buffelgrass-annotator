# Training Chips - Structure & Provenance

## Overview

This directory contains 1024x1024 pixel training chips extracted from source Cloud-Optimized GeoTIFFs (COGs) for buffelgrass segmentation annotation.

**Total chips:** 976 (1 per source COG)  
**Format:** PNG (RGB, 1024x1024)  
**Size per chip:** ~1-3 MB  
**Total dataset size:** ~1-3 GB

---

## Directory Structure

Chips are distributed across 100 subdirectories (00-99) for efficient filesystem performance:

```
data/training_chips/
├── 00/
│   ├── cap-29845_3210_1567_1024_1024.png
│   ├── cap-30123_8901_2345_1024_1024.png
│   └── ...
├── 01/
├── 02/
...
└── 99/
```

Each subdirectory contains ~10 chips. Distribution is based on hash of source image name.

---

## Chip Naming Convention

**Format:** `{source_image}_{ulx}_{uly}_{width}_{height}.png`

**Example:** `cap-29792_6666_4691_1024_1024.png`

Breaking this down:
- `cap-29792`: Source COG filename (from `gs://tumamoc-2023/cogs/cap-29792.tif`)
- `6666`: Upper-left X coordinate (pixels)
- `4691`: Upper-left Y coordinate (pixels)
- `1024`: Chip width (pixels)
- `1024`: Chip height (pixels)

**Lower-right corner** = (ULX + width, ULY + height) = (7690, 5715)

---

## Provenance Tracking

The naming convention encodes complete provenance, allowing you to:

### 1. Identify Source Image
```bash
# From chip filename cap-29792_6666_4691_1024_1024.png
# Source COG is: gs://tumamoc-2023/cogs/cap-29792.tif
```

### 2. Extract Exact Coordinates
```bash
python scripts/chip_info.py data/training_chips/34/cap-29792_6666_4691_1024_1024.png -v

# Output:
# Source Image:  cap-29792
# Upper Left:    (6666, 4691)
# Lower Right:   (7690, 5715)
# Dimensions:    1024 x 1024
```

### 3. Recreate Chip from Source
If you need to regenerate a chip (e.g., different size or format):

```bash
python scripts/chip_extractor.py \
    gs://tumamoc-2023/cogs/cap-29792.tif \
    --ulx 6666 --uly 4691 \
    --width 1024 --height 1024 \
    -o /tmp/recreated_chip.png
```

### 4. Find Chips from Specific Source Image
```bash
# All chips from cap-29792
find data/training_chips -name "cap-29792_*.png"
```

---

## Usage in Annotation Workflow

### CVAT Import
1. **Option A: Import all chips**
   ```bash
   find data/training_chips -name "*.png" > chip_list.txt
   # Upload via CVAT web UI
   ```

2. **Option B: Import from specific subdirectory**
   ```bash
   # Smaller batches for collaborative annotation
   ls data/training_chips/00/*.png
   ```

### Splitting for Multiple Annotators
```bash
make split-dataset
# This maintains provenance in split directories
```

---

## Quality Control

### Verify Chip Extraction
```bash
# Check chip count (should be 976)
find data/training_chips -name "*.png" | wc -l

# Check chip sizes
find data/training_chips -name "*.png" -exec file {} \; | head

# Should all report: PNG image data, 1024 x 1024
```

### Sample Chips by Coverage
```bash
# High vegetation coverage (typically in subdirs with more green areas)
# Use chip_info.py to trace back to source and select diverse examples
```

---

## Best Practices

### Annotation
- **Traceability:** Always keep original chip filenames in CVAT
- **Quality issues:** Note chip filename when reporting problems
- **Edge cases:** Use `chip_info.py` to find neighboring chips from same source

### Data Management
- **Backups:** Subdirectory structure makes rsync/backup efficient
- **Version control:** Don't commit chips to git (they're in .gitignore)
- **Cloud storage:** Upload to GCS for sharing with collaborators

---

## Helpful Commands

```bash
# Count chips per subdirectory
for dir in data/training_chips/*/; do
    echo "$(basename $dir): $(ls $dir/*.png 2>/dev/null | wc -l)"
done

# Find chips with specific coordinate range
# (e.g., upper-left X between 5000-6000)
find data/training_chips -name "*_5[0-9][0-9][0-9]_*_1024_1024.png"

# Get provenance for all chips from one COG
for chip in $(find data/training_chips -name "cap-29792_*.png"); do
    python scripts/chip_info.py "$chip"
done
```

---

## Generation Details

**Script:** `scripts/batch_extract_chips.py`  
**Extraction method:** Random 1024x1024 windows (not intersecting image boundaries)  
**Source:** `gs://tumamoc-2023/cogs/` (976 COG files, ~140 GB total)  
**Date generated:** 2025-10-30

To regenerate or add more chips:
```bash
make extract-chips
```

---

*For questions about chip provenance or to report issues, use `scripts/chip_info.py` to extract source details.*



