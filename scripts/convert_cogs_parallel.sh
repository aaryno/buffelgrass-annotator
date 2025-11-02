#!/bin/bash
# Parallel COG conversion using multiple Cloud Shell sessions
# No Cloud Build required!

set -e

PROJECT_ID="asdm-399400"
GCS_BUCKET="tumamoc-2023"
SOURCE_PREFIX="source-jpg/"
COG_PREFIX="cogs/"
NUM_WORKERS="${1:-5}"  # Default to 5 parallel workers

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Parallel COG Conversion (Cloud Shell)                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Workers: $NUM_WORKERS parallel Cloud Shell sessions"
echo "Source: gs://$GCS_BUCKET/$SOURCE_PREFIX"
echo "Destination: gs://$GCS_BUCKET/$COG_PREFIX"
echo ""

# Create a worker script that processes every Nth file
cat > /tmp/cog_worker.py << 'WORKER_EOF'
#!/usr/bin/env python3
import os
import sys
import tempfile
from google.cloud import storage
import subprocess

GCS_BUCKET = "tumamoc-2023"
SOURCE_PREFIX = "source-jpg/"
COG_PREFIX = "cogs/"

def file_exists_in_gcs(bucket_name, blob_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False

def convert_jpeg_to_cog(source_file, dest_file):
    """Convert JPEG to COG using rio-cogeo"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # Download
    source_blob = bucket.blob(source_file)
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_in:
        source_blob.download_to_filename(tmp_in.name)
        input_path = tmp_in.name
    
    # Convert
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp_out:
        output_path = tmp_out.name
    
    try:
        subprocess.run([
            'rio', 'cogeo', 'create',
            input_path, output_path,
            '--overview-level', '5',
            '--overview-resampling', 'average'
        ], check=True, capture_output=True)
        
        # Upload
        dest_blob = bucket.blob(dest_file)
        dest_blob.upload_from_filename(output_path, content_type='image/tiff')
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass

def main():
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    num_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    print(f"Worker {worker_id+1}/{num_workers} starting...")
    
    # List all source files
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=SOURCE_PREFIX))
    source_files = [b.name for b in blobs if b.name.endswith('.jpg')]
    
    # Process every Nth file (where N = num_workers)
    my_files = [f for i, f in enumerate(source_files) if i % num_workers == worker_id]
    
    print(f"Worker {worker_id+1}: Processing {len(my_files)} files")
    
    success = 0
    for i, source_file in enumerate(my_files, 1):
        filename = os.path.basename(source_file)
        dest_file = f"{COG_PREFIX}{filename.replace('.jpg', '.tif')}"
        
        # Skip if exists
        if file_exists_in_gcs(GCS_BUCKET, dest_file):
            print(f"  [{i}/{len(my_files)}] ⊘ {filename} (exists)")
            success += 1
            continue
        
        print(f"  [{i}/{len(my_files)}] 🔄 {filename}...", end='', flush=True)
        if convert_jpeg_to_cog(source_file, dest_file):
            print(" ✓")
            success += 1
        else:
            print(" ✗")
    
    print(f"\nWorker {worker_id+1} complete: {success}/{len(my_files)} successful")

if __name__ == "__main__":
    main()
WORKER_EOF

chmod +x /tmp/cog_worker.py

# Upload worker script to Cloud Shell
echo "📤 Uploading worker script to Cloud Shell..."
gcloud cloud-shell scp localhost:/tmp/cog_worker.py cloudshell:~/cog_worker.py

# Launch workers in parallel
echo ""
echo "🚀 Launching $NUM_WORKERS parallel workers..."
echo ""

for ((i=0; i<$NUM_WORKERS; i++)); do
    LOG_FILE="/tmp/cog_worker_${i}.log"
    echo "  Starting worker $((i+1))/$NUM_WORKERS (log: $LOG_FILE)"
    
    gcloud cloud-shell ssh --authorize-session --command="
        pip install rasterio rio-cogeo google-cloud-storage --quiet
        export PATH=\$PATH:\$HOME/.local/bin
        python3 ~/cog_worker.py $i $NUM_WORKERS
    " > "$LOG_FILE" 2>&1 &
    
    sleep 1  # Stagger starts
done

echo ""
echo "✓ All $NUM_WORKERS workers launched!"
echo ""
echo "Monitor progress:"
echo "  tail -f /tmp/cog_worker_*.log"
echo "  make status"
echo ""
echo "Workers will run in parallel and auto-skip completed files."
echo "Cloud Shell sessions will timeout after ~30 min - just re-run to resume!"



