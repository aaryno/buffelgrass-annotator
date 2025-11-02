================================================================================
  CVAT Buffelgrass Annotation Tool - Windows Package
================================================================================

QUICK START:
------------
1. Install Docker Desktop for Windows (if not already installed)
   Download from: https://www.docker.com/products/docker-desktop

2. Start Docker Desktop (wait for it to fully start)

3. Double-click: START-CVAT.bat

4. Wait 2-3 minutes for first-time setup

5. Browser will open to http://localhost:8080

6. Login with:
   Username: annotator
   Password: buffelgrass2024


ADDING YOUR TRAINING CHIPS:
----------------------------
Place your PNG/JPEG training images in:
  data\training_chips\

The CVAT server will automatically see files in this directory.


CREATING YOUR ANNOTATION PROJECT:
----------------------------------
1. Login to CVAT
2. Click "Projects" → "Create new project"
3. Project name: "My Buffelgrass Annotations"
4. Add labels (click "Add label"):
   - buffelgrass (primary target)
   - soil
   - road
   - building
   - car
   - tree_shrub
   - cactus
   - other_grass
5. Click "Submit"

6. Create a task:
   - Click "Tasks" → "Create new task"
   - Select your project
   - Click "Select files" → "Connected file share"
   - Select images from the share directory
   - Click "Submit"

7. Start annotating!


SHARING WITH OTHER COLLABORATORS:
----------------------------------
Each collaborator should:
1. Get their own copy of this windows-package folder
2. Put their assigned chips in their own data\training_chips\ folder
3. Run START-CVAT.bat on their machine
4. Create their own project or import the shared project

To share annotations:
- Export project: Projects → Select project → Actions → Export
- Send the .zip file to collaborators
- They import: Projects → Import → Select .zip file


STOPPING CVAT:
--------------
Double-click: STOP-CVAT.bat

Your annotations are saved and will be available next time!


COMMON ISSUES:
--------------
Q: "Docker Desktop is not running" error
A: Start Docker Desktop from Start Menu, wait for it to fully start

Q: Can't access http://localhost:8080
A: Wait 2-3 minutes after starting. Check Docker Desktop is running.

Q: Images don't appear in CVAT
A: Make sure images are in data\training_chips\ directory
   Restart CVAT: STOP-CVAT.bat, then START-CVAT.bat

Q: Forgot password
A: Run RESET-PASSWORD.bat (creates new user 'annotator')


TECHNICAL DETAILS:
------------------
- CVAT uses docker-compose with 10 containers
- Data is stored in Docker volumes (survives restarts)
- Training chips are mounted from: .\data\training_chips\
- Annotations are stored in Docker volume: cvat_data
- Port used: 8080 (make sure it's not in use by other programs)


SYSTEM REQUIREMENTS:
--------------------
- Windows 10/11 Pro, Enterprise, or Education (Home edition: use WSL2)
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Docker Desktop for Windows
- Internet connection (first-time setup only)


BACKUP YOUR WORK:
-----------------
Export your project regularly:
  Projects → Your Project → Actions → Export

This creates a .zip file with all annotations.


SUPPORT:
--------
For CVAT documentation: https://opencv.github.io/cvat/docs/
For Docker issues: https://docs.docker.com/desktop/windows/


================================================================================

