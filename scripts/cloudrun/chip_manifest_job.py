#!/usr/bin/env python3
"""
Cloud Run Job: Generate chip manifest for all COGs.

Pre-computes 6×5 grid (30 chips) for each COG and assigns to 625 bins (AA-YY).
Outputs manifest CSV to GCS for later sampling.

Environment Variables:
    TASK_INDEX: Cloud Run task index
    TASK_COUNT: Total number of parallel tasks
    SOURCE_BUCKET: Source bucket (default: tumamoc-2023)
    SOURCE_PREFIX: COG prefix (default: cogs/)
    OUTPUT_BUCKET: Output bucket (default: tumamoc-2023)
    OUTPUT_PATH: Output CSV path (default: chip-manifest.csv)
"""

import os
import sys
import csv
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
from google.cloud import storage

# Configure GDAL for GCS access
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'


def get_gcloud_access_token():
    """Get GCS access token for rasterio."""
    # In Cloud Run, use metadata server
    import requests
    metadata_server = "http://metadata.google.internal/computeMetadata/v1/"
    token_url = metadata_server + "instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    
    try:
        response = requests.get(token_url, headers=headers)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Warning: Could not get access token from metadata server: {e}")
        return None


# Set up GCS credentials for rasterio
token = get_gcloud_access_token()
if token:
    os.environ['GS_OAUTH2_TOKEN'] = token


import rasterio  # Import after setting up credentials


def generate_bin_labels(num_bins=625):
    """Generate 625 bin labels: AA through YY."""
    letters = [chr(65 + i) for i in range(25)]  # A-Y
    bins = []
    for first in letters:
        for second in letters:
            bins.append(first + second)
    return bins


def generate_random_token():
    """Generate random 2-letter token (aa-zz) for filename uniqueness."""
    import random
    letters = [chr(97 + i) for i in range(26)]  # a-z (lowercase)
    return ''.join(random.choices(letters, k=2))


def hash_to_bin(value: str, num_bins: int = 625) -> int:
    """Hash a value to a bin index."""
    hash_value = int(hashlib.md5(value.encode()).hexdigest(), 16)
    return hash_value % num_bins


def compute_chip_grid(width: int, height: int, chip_size: int = 1024,
                      grid_x: int = 6, grid_y: int = 5, margin: int = 10) -> List[Tuple[int, int]]:
    """Compute non-overlapping 6×5 chip grid."""
    required_width = (grid_x * chip_size) + (2 * margin)
    required_height = (grid_y * chip_size) + (2 * margin)
    
    if width < required_width or height < required_height:
        return []
    
    usable_width = width - (2 * margin)
    usable_height = height - (2 * margin)
    
    spacing_x = (usable_width - (grid_x * chip_size)) // (grid_x - 1) if grid_x > 1 else 0
    spacing_y = (usable_height - (grid_y * chip_size)) // (grid_y - 1) if grid_y > 1 else 0
    
    chips = []
    for row in range(grid_y):
        for col in range(grid_x):
            ulx = margin + (col * (chip_size + spacing_x))
            uly = margin + (row * (chip_size + spacing_y))
            
            if ulx + chip_size <= width - margin and uly + chip_size <= height - margin:
                chips.append((ulx, uly))
    
    return chips


def process_cog(bucket_name: str, cog_path: str, bin_labels: List[str]) -> List[Dict]:
    """Process single COG and generate manifest entries."""
    image_name = Path(cog_path).stem
    gs_path = f"gs://{bucket_name}/{cog_path}"
    
    try:
        # Read COG metadata (streaming, no download)
        with rasterio.open(gs_path) as src:
            width = src.width
            height = src.height
        
        # Compute chip grid
        chip_coords = compute_chip_grid(width, height)
        
        if not chip_coords:
            print(f"  ✗ {image_name}: Image too small ({width}×{height})")
            return []
        
        # Generate manifest entries
        entries = []
        for idx, (ulx, uly) in enumerate(chip_coords):
            bin_key = f"{image_name}_{idx}"
            bin_idx = hash_to_bin(bin_key, len(bin_labels))
            bin_label = bin_labels[bin_idx].lower()
            
            # Add random 2-letter token for additional randomness
            random_token = generate_random_token()
            chip_filename = f"{bin_label}-{random_token}-{image_name}.png"
            chip_path = f"{bin_label}/{chip_filename}"
            
            entry = {
                'chip_path': chip_path,
                'source_image': image_name,
                'ulx': ulx,
                'uly': uly,
                'width': 1024,
                'height': 1024
            }
            entries.append(entry)
        
        print(f"  ✓ {image_name}: {len(entries)} chips ({width}×{height})")
        return entries
        
    except Exception as e:
        print(f"  ✗ {image_name}: Error - {e}")
        return []


def list_cogs(bucket_name: str, prefix: str) -> List[str]:
    """List all COG files."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    blobs = list(bucket.list_blobs(prefix=prefix))
    cog_paths = [
        blob.name for blob in blobs
        if blob.name.endswith('.tif') and not blob.name.endswith('/')
    ]
    
    return sorted(cog_paths)


def save_partial_manifest(entries: List[Dict], task_index: int) -> str:
    """Save partial manifest to temp file."""
    temp_file = f"/tmp/chip_manifest_task_{task_index}.csv"
    
    with open(temp_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['chip_path', 'source_image', 'ulx', 'uly', 'width', 'height'])
        writer.writeheader()
        writer.writerows(entries)
    
    return temp_file


def upload_partial_manifest(local_path: str, bucket_name: str, task_index: int):
    """Upload partial manifest to GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    gcs_path = f"chip_manifests/partial/task_{task_index:03d}.csv"
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type='text/csv')
    
    print(f"\n✓ Uploaded to gs://{bucket_name}/{gcs_path}")


def main():
    """Main Cloud Run job execution."""
    task_index = int(os.getenv('CLOUD_RUN_TASK_INDEX', '0'))
    task_count = int(os.getenv('CLOUD_RUN_TASK_COUNT', '1'))
    
    source_bucket = os.getenv('SOURCE_BUCKET', 'tumamoc-2023')
    source_prefix = os.getenv('SOURCE_PREFIX', 'cogs/')
    output_bucket = os.getenv('OUTPUT_BUCKET', 'tumamoc-2023')
    
    print("=" * 70)
    print(f"Chip Manifest Generator - Task {task_index + 1}/{task_count}")
    print("=" * 70)
    print(f"Source: gs://{source_bucket}/{source_prefix}")
    print(f"Output: gs://{output_bucket}/chip_manifests/")
    print()
    
    # Generate bin labels
    bin_labels = generate_bin_labels(625)
    print(f"Generated {len(bin_labels)} bin labels (AA-YY)")
    print()
    
    # List all COGs
    print("Listing COGs...")
    all_cogs = list_cogs(source_bucket, source_prefix)
    
    # Distribute COGs across tasks
    my_cogs = [cog for i, cog in enumerate(all_cogs) if i % task_count == task_index]
    
    print(f"Total COGs: {len(all_cogs)}")
    print(f"This task: {len(my_cogs)} COGs")
    print()
    
    if not my_cogs:
        print("✓ No COGs to process")
        return 0
    
    # Process COGs
    all_entries = []
    success_count = 0
    
    for i, cog_path in enumerate(my_cogs, 1):
        print(f"[{i}/{len(my_cogs)}] Processing...")
        entries = process_cog(source_bucket, cog_path, bin_labels)
        
        if entries:
            all_entries.extend(entries)
            success_count += 1
    
    # Save and upload partial manifest
    print()
    print("=" * 70)
    print(f"Task {task_index + 1} Complete")
    print("=" * 70)
    print(f"COGs processed: {success_count}/{len(my_cogs)}")
    print(f"Chips generated: {len(all_entries)}")
    
    if all_entries:
        temp_file = save_partial_manifest(all_entries, task_index)
        print(f"Saved to: {temp_file}")
        
        upload_partial_manifest(temp_file, output_bucket, task_index)
    
    print()
    print("✓ Task complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

