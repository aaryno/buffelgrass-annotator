#!/usr/bin/env python3
"""Extract chips for selected groups from manifest and upload to VM"""

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

# Selected groups for first annotation batch
SELECTED_GROUPS = ['ah', 'bt', 'dx', 'ej', 'ev', 'gx', 'il', 'kg', 'lt', 'ni', 
                   'pd', 'ra', 'rb', 'tr', 'vc', 'vq', 'vt', 'wk', 'xi', 'yo']

def extract_chip(row, bucket_name, output_bucket, output_prefix):
    """Extract a single chip from a COG and upload to GCS"""
    try:
        chip_path, source_image, x, y, width, height = row
        x, y, width, height = int(x), int(y), int(width), int(height)
        
        # Construct paths
        source_path = f"gs://{bucket_name}/cogs/{source_image}.tif"
        output_gcs_path = f"{output_prefix}{chip_path}"
        
        # Extract chip using rasterio window
        with rasterio.open(source_path) as src:
            window = Window(x, y, width, height)
            data = src.read(window=window)
            
            # Convert to RGB image (assuming 3 bands)
            if data.shape[0] >= 3:
                rgb = np.transpose(data[:3, :, :], (1, 2, 0))
            else:
                rgb = np.transpose(data, (1, 2, 0))
            
            # Normalize to 0-255 range
            if rgb.max() > 255:
                rgb = ((rgb - rgb.min()) / (rgb.max() - rgb.min()) * 255).astype('uint8')
            else:
                rgb = rgb.astype('uint8')
            
            # Save as PNG to temp file
            img = Image.fromarray(rgb)
            temp_file = f"/tmp/{Path(chip_path).name}"
            img.save(temp_file, 'PNG')
            
            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(output_bucket)
            blob = bucket.blob(output_gcs_path)
            blob.upload_from_filename(temp_file)
            
            # Clean up
            os.remove(temp_file)
            
            return True, chip_path
            
    except Exception as e:
        return False, f"{row[0]}: {str(e)[:100]}"

def main():
    # Configuration
    manifest_path = "/Users/aaryn/asdm/chip-manifest.csv"
    bucket_name = "tumamoc-2023"
    output_bucket = "tumamoc-2023"
    output_prefix = "training_chips/1024x1024/"
    max_workers = 20  # Parallel downloads
    
    # Setup GCS credentials
    os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
    os.environ['CPL_VSIL_CURL_USE_HEAD'] = 'NO'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser(
        '~/.config/gcloud/application_default_credentials.json'
    )
    
    print(f"🚀 Extracting chips for selected groups")
    print(f"   Groups: {', '.join(SELECTED_GROUPS)}")
    print(f"   Source: gs://{bucket_name}/cogs/")
    print(f"   Destination: gs://{output_bucket}/{output_prefix}")
    print()
    
    # Read manifest and filter for selected groups
    print("📋 Reading manifest...")
    with open(manifest_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        all_rows = [row for row in reader if len(row) == 6]
    
    # Filter for selected groups
    selected_rows = []
    for row in all_rows:
        chip_path = row[0]
        group = chip_path.split('/')[0]
        if group in SELECTED_GROUPS:
            selected_rows.append(row)
    
    total_chips = len(selected_rows)
    print(f"✅ Found {total_chips:,} chips in selected groups")
    print()
    
    # Count per group
    group_counts = {}
    for row in selected_rows:
        group = row[0].split('/')[0]
        group_counts[group] = group_counts.get(group, 0) + 1
    
    print("📊 Chips per group:")
    for group in SELECTED_GROUPS:
        count = group_counts.get(group, 0)
        print(f"   {group}: {count} chips")
    print()
    
    # Extract chips in parallel
    print(f"🔄 Extracting {total_chips:,} chips with {max_workers} workers...")
    print()
    
    completed = 0
    failed = 0
    errors = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_chip, row, bucket_name, output_bucket, output_prefix): row
            for row in selected_rows
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
                
                # Print progress every 10 chips
                if completed % 10 == 0 or completed == total_chips:
                    bar_len = 40
                    filled = int(bar_len * completed / total_chips)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    print(f"\r[{bar}] {percent:.1f}% | "
                          f"{completed}/{total_chips} | "
                          f"{rate:.1f} chips/sec | ETA: {eta/60:.1f}m", 
                          end='', flush=True)
            else:
                failed += 1
                if len(errors) < 5:  # Keep first 5 errors
                    errors.append(result)
    
    print()
    print()
    print("=" * 70)
    print(f"✅ Extraction complete!")
    print(f"   Successful: {completed - failed:,}/{total_chips:,} chips")
    if failed > 0:
        print(f"   Failed: {failed}")
        if errors:
            print(f"\n   First errors:")
            for err in errors:
                print(f"     - {err}")
    print(f"   Time: {(time.time() - start_time)/60:.1f} minutes")
    print(f"   Location: gs://{output_bucket}/{output_prefix}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())


