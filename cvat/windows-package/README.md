## CVAT Windows Package for Buffelgrass Annotation
**Arizona Sonoran Desert Museum - Collaborative Annotation Project**

### 📦 Package Contents

```
cvat-windows-package/
├── start-cvat.bat          # Double-click to start CVAT
├── stop-cvat.bat           # Double-click to stop CVAT
├── docker-compose.yml      # Container configuration
├── nginx.conf              # Web server config
├── setup-project.py        # Create shared buffelgrass project
├── README.md               # This file
├── chips/                  # PUT YOUR TRAINING IMAGES HERE
├── project/                # CVAT database (created automatically)
└── annotations/            # Exported annotations (created automatically)
```

### 🚀 Quick Start

#### 1. Prerequisites
- **Docker Desktop** installed ([Download here](https://docs.docker.com/desktop/setup/install/windows-install/))
- **Training chip images** provided by project coordinator

#### 2. Setup (5 minutes)

1. **Extract this package** to a location like:
   ```
   C:\Users\YourName\Documents\buffelgrass-annotation\
   ```

2. **Copy your assigned training chips** into the `chips\` folder:
   ```
   chips\
   ├── chip_001.tif
   ├── chip_002.tif
   ├── chip_003.tif
   └── ...
   ```

3. **Start Docker Desktop** and wait for it to fully load (green indicator)

4. **Double-click `start-cvat.bat`**
   - First run downloads images (~2 GB, takes 5-10 minutes)
   - Subsequent runs start immediately (~30 seconds)
   - Browser opens automatically to http://localhost:8080

#### 3. First-Time Account Setup

1. Register your account:
   - **Username**: Your name (e.g., `kaitlyn`)
   - **Email**: Your ASDM email
   - **Password**: Choose a secure password

2. Import shared project configuration:
   - Run `python setup-project.py --username kaitlyn` (replace with your username)
   - This creates the "Buffelgrass Detection" project with all labels
   - Creates a task with your training chips

### 🎨 Annotation Workflow

#### Daily Workflow
1. Double-click `start-cvat.bat`
2. Log in at http://localhost:8080
3. Open your task: "Buffelgrass Training Set"
4. Annotate 25-50 images per session
5. Click `Ctrl+S` frequently to save
6. When done, double-click `stop-cvat.bat`

#### Annotation Labels
The project includes 8 semantic labels:

| Label | Color | Description |
|-------|-------|-------------|
| **buffelgrass** | 🔴 Red | Primary target - invasive grass |
| soil | 🟤 Brown | Bare ground |
| road | ⬛ Gray | Roads, trails, paths |
| building | 🟣 Purple | Structures |
| car | 🟡 Gold | Vehicles |
| tree_shrub | 🌲 Forest Green | Native woody vegetation |
| cactus | 🌵 Bright Green | Native cacti |
| other_grass | 🟢 Light Green | Native grasses |

**Focus primarily on buffelgrass** - other labels are optional context.

#### Annotation Tools
- **Polygon** (N): Draw precise boundaries
- **Brush** (B): Paint regions
- **AI Polygon** (Shift+N): SAM-assisted segmentation (click buffelgrass)
- **Zoom**: Mouse wheel
- **Pan**: Hold Space + drag

#### Keyboard Shortcuts
- `F` - Next image
- `D` - Previous image
- `Ctrl+S` - Save
- `N` - Polygon mode
- `Esc` - Cancel current polygon

### 📤 Exporting Annotations

When you've completed your assigned images:

1. Click your task name → **Actions** → **Export task dataset**
2. Format: **COCO 1.0**
3. Click **Export** and download the ZIP file
4. Rename the file: `buffelgrass_annotations_YOURNAME.zip`
5. Send to project coordinator (via email/Dropbox)

### 🤝 Collaborative Setup

#### Sharing This Package
All annotators should receive:
1. This complete package folder
2. Their assigned training chips (in `chips/` folder)
3. Same Docker Compose configuration (already included)
4. Same project labels (via `setup-project.py`)

#### What Gets Shared?
✅ **Share with everyone:**
- `docker-compose.yml`
- `nginx.conf`
- `setup-project.py`
- Label definitions
- Annotation guidelines

❌ **Don't share:**
- `project/` folder (contains your personal annotations)
- Login credentials
- `annotations/` exports (send to coordinator only)

### 🔧 Troubleshooting

#### "Docker Desktop not found"
- Install Docker Desktop from link in error message
- Ensure it's in default location: `C:\Program Files\Docker\Docker\`
- Restart computer after installation

#### "Docker Desktop is not running"
- Open Docker Desktop application
- Wait for green "Engine running" indicator (1-2 minutes)
- Run `start-cvat.bat` again

#### "Cannot connect to http://localhost:8080"
- Wait 30-60 seconds - services are still starting
- Check Docker Desktop → Containers - all should show "Running"
- Try refreshing your browser

#### CVAT is slow
- Close other applications
- In CVAT: Settings → Reduce image quality to 75%
- Restart CVAT: `stop-cvat.bat` then `start-cvat.bat`

#### Lost annotations
- Check: **Jobs** → Your task → **Actions** → **Backup**
- Annotations auto-save every 2 minutes
- Database is in `project/` folder - don't delete it!

### 💾 Backup Your Work

**Important**: The `project/` folder contains ALL your annotations!

**Regular backups:**
1. Stop CVAT (`stop-cvat.bat`)
2. Copy entire `project/` folder to backup location
3. Or export from CVAT web UI weekly

### 📊 Progress Tracking

**Recommended pace:**
- 25-50 chips per session
- 3-5 sessions per week
- Takes 3-5 minutes per chip on average

**Check your progress:**
- CVAT shows: "Completed: X / Y"
- Goal: Complete all assigned chips

### ❓ Getting Help

**Issues? Questions?**
Contact project coordinator:
- Email: [coordinator email]
- Phone: [coordinator phone]

**CVAT Documentation:**
- User guide: https://opencv.github.io/cvat/docs/manual/
- Video tutorials: Search "CVAT annotation tutorial" on YouTube

### 🎯 Annotation Quality Tips

1. **Consistency matters more than perfection**
   - Use same criteria throughout
   - Compare with example annotations
   - Ask coordinator if uncertain

2. **Focus on buffelgrass boundaries**
   - Follow grass edges closely
   - Don't include too much background
   - Separate distinct clumps

3. **Take breaks**
   - Every 30-45 minutes
   - Prevents annotation fatigue
   - Maintains quality

4. **Save frequently**
   - Press `Ctrl+S` every 5-10 images
   - Annotations auto-save every 2 minutes
   - Better safe than sorry!

### 📝 Version Information

- **CVAT Version**: 2.10.0
- **Docker Compose**: v3.8
- **Required**: Docker Desktop 4.0+
- **Tested on**: Windows 10/11

---

**Thank you for contributing to the Buffelgrass Mapping Project!** 🌵

Your annotations will help create AI models to map invasive buffelgrass
across the Sonoran Desert, supporting conservation efforts at ASDM and beyond.


