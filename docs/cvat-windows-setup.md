# CVAT Setup Guide for Windows

Complete guide for setting up CVAT (Computer Vision Annotation Tool) on Windows for buffelgrass annotation.

---

## 📋 Prerequisites

### System Requirements
- **OS:** Windows 10/11 (64-bit)
- **RAM:** 8 GB minimum, 16 GB recommended
- **Disk:** 20 GB free space (plus space for your image dataset)
- **Internet:** Required for initial setup

---

## 🚀 Step 1: Install Docker Desktop

### 1.1 Download Docker Desktop
1. Visit: https://www.docker.com/products/docker-desktop
2. Click **"Download for Windows"**
3. Run the installer: `Docker Desktop Installer.exe`

### 1.2 Enable WSL2 (Required)
Docker Desktop will prompt you to install WSL2. If not:

1. Open **PowerShell as Administrator**
2. Run:
```powershell
wsl --install
```
3. Restart your computer
4. After restart, open **Ubuntu** from Start menu (it will auto-install)
5. Create a username and password when prompted

### 1.3 Configure Docker Desktop
1. Open **Docker Desktop**
2. Go to **Settings** (gear icon)
3. **Resources → Advanced:**
   - CPUs: 4 (or half of your total)
   - Memory: 8 GB (or half of your total RAM)
4. Click **Apply & Restart**

### 1.4 Verify Installation
Open **PowerShell** and run:
```powershell
docker --version
docker compose version
```

You should see version numbers (e.g., `Docker version 24.0.7`)

✅ **Docker is ready!**

---

## 💻 Step 2: Install CVAT

### 2.1 Install Git (if not installed)
1. Download: https://git-scm.com/download/win
2. Run installer with default settings
3. Restart PowerShell

### 2.2 Download CVAT
Open **PowerShell** and run:

```powershell
# Navigate to a folder where you want to install CVAT
cd C:\Users\YourUsername\Documents

# Clone CVAT
git clone https://github.com/opencv/cvat
cd cvat
```

### 2.3 Start CVAT
```powershell
# Start all CVAT services
docker compose up -d
```

**First time will take 5-10 minutes** to download all Docker images (~2-3 GB).

You'll see output like:
```
[+] Running 10/10
 ✔ Container cvat_redis        Started
 ✔ Container cvat_db           Started
 ✔ Container cvat_server       Started
 ✔ Container cvat_ui           Started
 ...
```

### 2.4 Verify CVAT is Running
```powershell
# Check status
docker compose ps
```

All services should show `Up` status.

---

## 🎨 Step 3: Access CVAT

### 3.1 Open CVAT in Browser
1. Open your web browser
2. Navigate to: **http://localhost:8080**
3. You should see the CVAT login page

### 3.2 Create Your Account
On first visit:
1. Click **"Create an account"**
2. Fill in:
   - **Username:** (your choice)
   - **Email:** (your email)
   - **Password:** (create a secure password)
   - **Confirm password:** (same password)
3. Click **"Submit"**
4. You'll be logged in automatically

✅ **CVAT is now running!**

---

## 📁 Step 4: Import Images

### Option A: Copy Images to Your Computer

#### 4.1 Create a Data Folder
```powershell
# Create folder for images
mkdir C:\Users\YourUsername\Documents\buffelgrass_chips
```

#### 4.2 Copy Images
**If you received images via USB drive:**
```powershell
# Copy from USB to your computer
xcopy E:\training_chips\*.png C:\Users\YourUsername\Documents\buffelgrass_chips\ /E /H /C /I
```

**If you received images via Dropbox/shared folder:**
1. Download the folder to your computer
2. Move to `C:\Users\YourUsername\Documents\buffelgrass_chips\`

### Option B: Import Directly in CVAT

#### 4.3 Create a New Project
1. In CVAT, click **"Projects"** (top menu)
2. Click **"+"** (Create new project)
3. Fill in:
   - **Name:** "Buffelgrass Segmentation - [Your Name]"
   - **Labels:** Click **"Add label"**
     - **Label name:** `buffelgrass`
     - **Type:** Check **"Polygon"** (for segmentation)
4. Click **"Submit"**

#### 4.4 Create a Task
1. Click on your project name
2. Click **"+"** (Create new task)
3. Fill in:
   - **Name:** "Region A - Batch 1" (or whatever makes sense)
   - **Subset:** Leave as **"Train"**
4. Under **"Select files":**
   - Click **"My computer"**
   - Click **"Select files"** button
   - Navigate to your images folder
   - Select images (Shift+Click to select multiple)
   - Click **"Open"**
5. **Important:** Set **"Image quality"** to **100** (for best annotation quality)
6. Click **"Submit"**

**Upload will take a few minutes** depending on number of images.

#### 4.5 Start Annotating
1. Click on your task name
2. Click **"Job #1"**
3. CVAT annotation interface will open!

---

## 🖊️ Step 5: Annotating Images

### Basic Controls
- **Draw polygon:** Click **"Draw new polygon"** (or press **N**)
- **Navigation:**
  - **F** = Next image
  - **D** = Previous image
  - **Ctrl+S** = Save
- **Zoom:**
  - Mouse wheel = Zoom in/out
  - Hold **Ctrl** and drag = Pan

### Annotation Tips
1. **Click to create polygon points** around buffelgrass
2. **Press N** to finish polygon (closes the shape)
3. **Right-click point** to delete it
4. **Ctrl+Z** to undo
5. **Save frequently!** (Ctrl+S)

### Annotation Guidelines for Buffelgrass
- Draw polygons around **visible buffelgrass clusters**
- Include the **whole clump** of grass
- Separate individual clumps = separate polygons
- If unsure, skip the image (press **F** to next)

---

## 💾 Step 6: Export Your Annotations

### When you're done annotating:

1. Go back to **Tasks** view (click **"Tasks"** in top menu)
2. Find your task
3. Click the **three dots (⋮)** → **"Export task dataset"**
4. Choose format: **"COCO 1.0"** (best for merging later)
5. Click **"Export"**
6. Download will start automatically

**Save this file!** You'll need it to merge with other annotators.

---

## 🔄 Step 7: Stopping/Starting CVAT

### Stop CVAT (When Done for the Day)
```powershell
cd C:\Users\YourUsername\Documents\cvat
docker compose stop
```

**This saves resources on your computer.**

### Start CVAT Again (Next Time)
```powershell
cd C:\Users\YourUsername\Documents\cvat
docker compose start
```

Then open: http://localhost:8080

**Your data is saved!** All annotations are preserved.

---

## 🆘 Troubleshooting

### Problem: "Port 8080 already in use"
**Solution:** Another program is using port 8080.

```powershell
# Find what's using port 8080
netstat -ano | findstr :8080

# Stop Docker and restart
docker compose down
docker compose up -d
```

### Problem: "Docker daemon is not running"
**Solution:** Start Docker Desktop from Start menu.

1. Search for **"Docker Desktop"** in Start menu
2. Click to open
3. Wait for Docker to start (whale icon in system tray)
4. Then retry: `docker compose up -d`

### Problem: CVAT won't load images
**Solution:** Check Docker has enough resources.

1. Docker Desktop → Settings → Resources
2. Increase **Memory** to 8-12 GB
3. Click **Apply & Restart**

### Problem: "Can't save annotations"
**Solution:** Check your internet connection and Docker status.

```powershell
# Check Docker containers
docker compose ps

# Restart if needed
docker compose restart
```

### Problem: Slow performance
**Solutions:**
1. Close other programs
2. Annotate in smaller batches (50-100 images per task)
3. Lower image quality to 75% (in task settings)

---

## 📞 Need Help?

### Common Commands Reference

```powershell
# Start CVAT
cd C:\Users\YourUsername\Documents\cvat
docker compose up -d

# Stop CVAT
docker compose stop

# Restart CVAT
docker compose restart

# View logs (if something's wrong)
docker compose logs

# Completely remove CVAT (keeps your data)
docker compose down

# Remove CVAT and all data (CAREFUL!)
docker compose down -v
```

### Check CVAT Documentation
- Official docs: https://opencv.github.io/cvat/docs/
- Video tutorials: Search YouTube for "CVAT annotation tutorial"

---

## ✅ Quick Start Checklist

- [ ] Docker Desktop installed and running
- [ ] WSL2 enabled
- [ ] CVAT cloned and running (`docker compose up -d`)
- [ ] Accessed CVAT at http://localhost:8080
- [ ] Created account
- [ ] Created project with "buffelgrass" label
- [ ] Created task and uploaded images
- [ ] Started annotating!
- [ ] Exported annotations as COCO format

---

## 📧 Sharing Your Work

### When Ready to Share Annotations:

1. **Export your annotations** (Step 6 above)
2. **File will be named:** `task_buffelgrass-2025_10_29.zip` (or similar)
3. **Share via:**
   - Email (if small)
   - Dropbox/Google Drive link
   - USB drive
   - Cloud storage

**Send the exported file** to the project coordinator for merging!

---

## 🎯 Tips for Efficient Annotation

1. **Set a goal:** Annotate 25-50 images per session
2. **Take breaks:** Every 30-45 minutes
3. **Save frequently:** Ctrl+S every 5-10 images
4. **Use keyboard shortcuts:** Much faster than mouse
5. **Consistent labeling:** When in doubt, ask for clarification
6. **Quality over quantity:** Accurate annotations are better than many poor ones

---

**Happy Annotating!** 🌿

Questions? Contact: [Your Email/Phone]



