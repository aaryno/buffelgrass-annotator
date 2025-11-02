#!/usr/bin/env python3
"""
Multi-threaded COG converter - runs in a single Cloud Shell session
with multiple worker threads for parallel processing.
"""

import os
import sys
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from google.cloud import storage

# Configuration
GCS_BUCKET = "tumamoc-2023"
SOURCE_PREFIX = "source-jpg/"
COG_PREFIX = "cogs/"
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "8"))  # 8 parallel threads

# Progress tracking
progress_lock = Lock()
stats = {"processed": 0, "skipped": 0, "failed": 0, "total": 0}

def file_exists_in_gcs(bucket_name, blob_name):
    """Check if file exists in GCS"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False

def convert_one_file(source_file):
    """Convert a single JPEG to COG"""
    filename = os.path.basename(source_file)
    dest_file = f"{COG_PREFIX}{filename.replace('.jpg', '.tif')}"
    
    # Skip if exists
    if file_exists_in_gcs(GCS_BUCKET, dest_file):
        with progress_lock:
            stats["skipped"] += 1
            stats["processed"] += 1
            pct = (stats["processed"] / stats["total"]) * 100
            print(f"  [{stats['processed']}/{stats['total']}] ({pct:5.1f}%) ⊘ {filename} (exists)")
        return True
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    
    try:
        # Download
        source_blob = bucket.blob(source_file)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_in:
            source_blob.download_to_filename(tmp_in.name)
            input_path = tmp_in.name
        
        # Convert to COG
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp_out:
            output_path = tmp_out.name
        
        subprocess.run([
            'rio', 'cogeo', 'create',
            input_path, output_path,
            '--overview-level', '5',
            '--overview-resampling', 'average',
            '--web-optimized'
        ], check=True, capture_output=True, text=True)
        
        # Upload
        dest_blob = bucket.blob(dest_file)
        dest_blob.upload_from_filename(output_path, content_type='image/tiff')
        
        # Cleanup
        os.unlink(input_path)
        os.unlink(output_path)
        
        with progress_lock:
            stats["processed"] += 1
            pct = (stats["processed"] / stats["total"]) * 100
            print(f"  [{stats['processed']}/{stats['total']}] ({pct:5.1f}%) ✓ {filename}")
        
        return True
        
    except Exception as e:
        with progress_lock:
            stats["failed"] += 1
            stats["processed"] += 1
            pct = (stats["processed"] / stats["total"]) * 100
            print(f"  [{stats['processed']}/{stats['total']}] ({pct:5.1f}%) ✗ {filename}: {str(e)[:60]}")
        return False

def main():
    print(f"\n╔{'═'*66}╗")
    print(f"║  Multi-threaded COG Converter ({NUM_WORKERS} workers)".ljust(66) + " ║")
    print(f"╚{'═'*66}╝\n")
    
    # List all source files
    print("📋 Listing source files...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=SOURCE_PREFIX))
    source_files = [b.name for b in blobs if b.name.endswith('.jpg')]
    
    stats["total"] = len(source_files)
    print(f"   Found {stats['total']} source JPEGs\n")
    
    print(f"🚀 Starting {NUM_WORKERS} parallel workers...\n")
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(convert_one_file, f): f for f in source_files}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  Worker exception: {e}")
    
    # Summary
    print(f"\n{'═'*70}")
    print(f"✓ Conversion complete!")
    print(f"  Total:   {stats['total']}")
    print(f"  Success: {stats['total'] - stats['failed'] - stats['skipped']}")
    print(f"  Skipped: {stats['skipped']} (already existed)")
    print(f"  Failed:  {stats['failed']}")
    print(f"{'═'*70}\n")

if __name__ == "__main__":
    main()



