#!/usr/bin/env python3
"""Extract chips from COGs based on chip-manifest.csv"""

import os
import sys
import csv
from pathlib import Path
from google.cloud import storage
import rasterio
from rasterio.windows import Window
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def extract_chip(row, bucket_name, local_cache_dir, output_bucket, output_prefix):
    """Extract a single chip from a COG and upload to GCS"""
    try:
        output_path, source_image, x, y, width, height = row
        x, y, width, height = int(x), int(y), int(width), int(height)
        
        # Construct paths
        source_path = f"gs://{bucket_name}/cogs/{source_image}.tif"
        output_gcs_path = f"{output_prefix}{output_path}"
        
        # Extract chip using rasterio window
        with rasterio.open(source_path) as src:
            window = Window(x, y, width, height)
            data = src.read(window=window)
            
            # Convert to RGB image (assuming 3 bands)
            if data.shape[0] >= 3:
                rgb = np.transpose(data[:3, :, :], (1, 2, 0))
            else:
                rgb = np.transpose(data, (1, 2, 0))
            
            # Save as PNG to temp file
            img = Image.fromarray(rgb.astype('uint8'))
            temp_file = f"/tmp/{Path(output_path).name}"
            img.save(temp_file, 'PNG')
            
            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(output_bucket)
            blob = bucket.blob(output_gcs_path)
            blob.upload_from_filename(temp_file)
            
            # Clean up
            os.remove(temp_file)
            
            return True, output_path
            
    except Exception as e:
        return False, f"{output_path}: {e}"

def main():
    # Configuration
    manifest_path = "/Users/aaryn/asdm/chip-manifest.csv"
    bucket_name = "tumamoc-2023"
    output_bucket = "tumamoc-2023"
    output_prefix = "training_chips/1024x1024/"
    cache_dir = "/tmp/cog_cache"
    max_workers = 10  # Parallel downloads
    
    # Setup GCS credentials
    os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
    os.environ['CPL_VSIL_CURL_USE_HEAD'] = 'NO'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    
    print(f"🚀 Extracting chips from manifest: {manifest_path}")
    print(f"   Source: gs://{bucket_name}/cogs/")
    print(f"   Destination: gs://{output_bucket}/{output_prefix}")
    print()
    
    # Read manifest
    with open(manifest_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        rows = [row for row in reader if len(row) == 6]  # Filter valid rows
    
    total_chips = len(rows)
    print(f"📊 Found {total_chips:,} chips to extract")
    print()
    
    # Extract chips in parallel
    completed = 0
    failed = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_chip, row, bucket_name, cache_dir, output_bucket, output_prefix): row
            for row in rows
        }
        
        for future in as_completed(futures):
            success, result = future.result()
            completed += 1
            
            if success:
                # Progress indicator
                percent = (completed / total_chips) * 100
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_chips - completed) / rate if rate > 0 else 0
                
                # Print progress every 10 chips or at milestones
                if completed % 10 == 0 or completed == total_chips:
                    print(f"\r[{completed}/{total_chips}] {percent:.1f}% | "
                          f"{rate:.1f} chips/sec | ETA: {eta/60:.1f} min", end='', flush=True)
            else:
                failed += 1
                if failed <= 5:  # Only show first 5 errors
                    print(f"\n❌ Failed: {result}")
    
    print()
    print()
    print("=" * 60)
    print(f"✅ Extraction complete!")
    print(f"   Successful: {completed - failed:,}/{total_chips:,} chips")
    print(f"   Failed: {failed}")
    print(f"   Time: {(time.time() - start_time)/60:.1f} minutes")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())


