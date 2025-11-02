# CVAT Setup for Windows Collaborators

## Option 1: Remote Access (Easiest) ⭐

Share your Mac's CVAT instance over the network - no Windows setup needed!

### On Mac (Host)

```bash
# 1. Find your local IP address
ipconfig getifaddr en0  # WiFi
# or
ipconfig getifaddr en1  # Ethernet

# Example output: 192.168.1.100
```

```bash
# 2. Update CVAT to allow external access
cd ~/cvat
# Edit docker-compose.yml to expose port externally
```

### On Windows (Collaborator)

Simply open browser to: `http://YOUR_MAC_IP:8080`

**Example**: `http://192.168.1.100:8080`

Then log in with shared credentials!

**Pros:**
- ✅ No setup required on Windows
- ✅ All data stays on Mac
- ✅ Annotations sync automatically
- ✅ Works over LAN or VPN

**Cons:**
- ⚠️ Mac must be running
- ⚠️ Both must be on same network (or use VPN/tunnel)

---

## Option 2: Full Windows Installation

Install CVAT directly on Windows machine.

### Prerequisites (Windows)

1. **Install Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop
   - Requires Windows 10/11 Pro, Enterprise, or Education
   - Enable WSL 2 backend

2. **Install Git for Windows**
   - Download from: https://git-scm.com/download/win

### Setup Steps (PowerShell)

```powershell
# 1. Clone CVAT
git clone https://github.com/opencv/cvat.git
cd cvat

# 2. Start CVAT
docker-compose up -d

# 3. Wait for startup (2-3 minutes)
Start-Sleep -Seconds 120

# 4. Access CVAT
# Open browser to: http://localhost:8080
```

### Share Project Export/Import

**Export from Mac:**
```bash
# Create export package
cd ~/asdm
python3 cvat/export-project.py
# Creates: buffelgrass-detection-export.zip
```

**Import on Windows:**
1. Open CVAT at http://localhost:8080
2. Login/create account
3. Go to Projects → Import
4. Upload `buffelgrass-detection-export.zip`
5. Start annotating!

**Pros:**
- ✅ Independent setup
- ✅ Can work offline
- ✅ Full control

**Cons:**
- ⚠️ Requires Docker Desktop (Windows Pro/Enterprise)
- ⚠️ Need to sync annotations manually
- ⚠️ Uses ~8GB RAM

---

## Option 3: Cloud VM (Best for Multiple Collaborators)

Deploy CVAT on GCP VM - accessible to everyone via URL.

### Setup (Run on Mac)

```bash
# Deploy to GCP
cd ~/asdm/geti-vm

# Create VM and install CVAT
gcloud compute instances create cvat-shared \
    --project=asdm \
    --zone=us-west1-b \
    --machine-type=e2-standard-4 \
    --boot-disk-size=100GB \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server
    
# SSH and install
gcloud compute ssh cvat-shared --zone=us-west1-b
# Follow installation steps from geti-vm/README.md
```

### Access (Mac & Windows)

Both users access: `http://VM_EXTERNAL_IP:8080`

**Get VM IP:**
```bash
gcloud compute instances describe cvat-shared \
    --zone=us-west1-b \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

**Pros:**
- ✅ Accessible from anywhere
- ✅ Multiple collaborators
- ✅ Always available
- ✅ Better performance

**Cons:**
- ⚠️ Costs ~$100-150/month if always on
- ⚠️ Requires GCP setup

---

## Option 4: Share via Tunneling (ngrok)

Expose your Mac's CVAT to the internet temporarily.

### Setup (Mac)

```bash
# 1. Install ngrok
brew install ngrok

# 2. Create tunnel
ngrok http 8080

# 3. Share the public URL with collaborator
# Example: https://abc123.ngrok.io
```

### Access (Windows)

Open browser to the ngrok URL provided.

**Pros:**
- ✅ Quick setup
- ✅ Works from anywhere
- ✅ No cloud costs

**Cons:**
- ⚠️ Free tier has limitations
- ⚠️ URL changes each time
- ⚠️ Mac must stay on

---

## Recommended Approach

### For 1-2 collaborators on same network:
→ **Option 1: Remote Access**

### For 2-5 collaborators, short-term project:
→ **Option 4: ngrok tunneling**

### For 5+ collaborators or long-term:
→ **Option 3: Cloud VM**

### For independent work with occasional sync:
→ **Option 2: Windows Installation**

---

## Windows-Specific Commands

### PowerShell equivalents to Mac commands:

| Mac (bash) | Windows (PowerShell) |
|------------|---------------------|
| `ls` | `Get-ChildItem` or `dir` |
| `cd ~/directory` | `cd C:\Users\YourName\directory` |
| `export VAR=value` | `$env:VAR="value"` |
| `make cvat-start` | _(not available, use docker-compose directly)_ |

### Docker Compose Commands (Windows)

```powershell
# Start CVAT
docker-compose up -d

# Stop CVAT
docker-compose stop

# View logs
docker-compose logs -f

# Check status
docker ps
```

---

## Sharing Credentials

Create a shared `.cvat.env` file:

```bash
CVAT_HOST=http://YOUR_SERVER_IP:8080
CVAT_USERNAME=team-annotator
CVAT_PASSWORD=SecurePassword123!
CVAT_EMAIL=team@localhost
```

**Security Note**: Share credentials securely (password manager, encrypted file, etc.)

---

## Annotation Workflow for Teams

1. **Project Lead (You)**: Create project, upload images
2. **Assign Tasks**: Divide images among annotators
3. **Collaborators**: Access CVAT, annotate assigned images
4. **Review**: Lead reviews annotations
5. **Export**: Lead exports final annotations for training

### Task Assignment in CVAT

1. Create multiple tasks within same project
2. Assign each task to different user
3. Each user sees only their assigned images
4. All use same label set (8 semantic classes)

---

## Troubleshooting

### Windows can't connect to Mac CVAT

1. Check firewall allows port 8080
2. Verify both on same network
3. Try Mac IP address directly

### Docker won't start on Windows

1. Ensure WSL 2 is enabled
2. Check Docker Desktop is running
3. Verify Windows version (needs Pro/Enterprise)

### Slow annotation performance

1. Reduce image resolution
2. Use cloud VM instead
3. Close other applications

---

## Next Steps

1. Choose collaboration method
2. Set up access for Windows user
3. Create user account for collaborator
4. Assign annotation tasks
5. Start team annotation!


