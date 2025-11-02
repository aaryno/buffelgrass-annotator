#!/usr/bin/env python3
"""
Check dimensions of source COGs and calculate max non-overlapping chips.

Samples COGs to determine typical dimensions and how many 1024x1024
chips can be extracted without overlap.
"""

import sys
import os
import subprocess
import rasterio
from google.cloud import storage
from pathlib import Path
import statistics

# Get access token from gcloud configuration 'asdm'
def get_gcloud_access_token(config='asdm'):
    """Get access token from specific gcloud configuration."""
    # Try to find gcloud in common locations
    gcloud_paths = [
        '/opt/homebrew/bin/gcloud',
        '/usr/local/bin/gcloud',
        '/opt/homebrew/share/google-cloud-sdk/bin/gcloud',
        'gcloud'  # fallback to PATH
    ]
    
    gcloud_cmd = None
    for path in gcloud_paths:
        if os.path.exists(path) or path == 'gcloud':
            gcloud_cmd = path
            break
    
    if not gcloud_cmd:
        raise FileNotFoundError("gcloud command not found")
    
    result = subprocess.run(
        [gcloud_cmd, '--configuration', config, 'auth', 'print-access-token'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

# Set up GDAL/rasterio to use gcloud access token
try:
    access_token = get_gcloud_access_token('asdm')
    os.environ['GS_OAUTH2_TOKEN'] = access_token
    os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
    os.environ['CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE'] = 'NO'
except Exception as e:
    print(f"Warning: Could not get gcloud access token: {e}")
    print("Trying with application default credentials...")
    # Fall back to application default credentials if available


def get_cog_dimensions(bucket_name, cog_path):
    """Get dimensions of a COG from GCS."""
    gs_path = f"gs://{bucket_name}/{cog_path}"
    with rasterio.open(gs_path) as src:
        return src.width, src.height


def calculate_max_chips(width, height, chip_size=1024, margin=10):
    """
    Calculate maximum non-overlapping chips.
    
    Args:
        width: Image width
        height: Image height
        chip_size: Chip size (default 1024x1024)
        margin: Edge margin (default 10px)
        
    Returns:
        (num_chips_x, num_chips_y, total_chips)
    """
    usable_width = width - (2 * margin)
    usable_height = height - (2 * margin)
    
    num_chips_x = usable_width // chip_size
    num_chips_y = usable_height // chip_size
    total_chips = num_chips_x * num_chips_y
    
    return num_chips_x, num_chips_y, total_chips


def sample_cogs(bucket_name, prefix, num_samples=10):
    """Sample COG dimensions from GCS bucket."""
    storage_client = storage.Client(project='asdm')
    bucket = storage_client.bucket(bucket_name)
    
    # Get all COGs
    blobs = list(bucket.list_blobs(prefix=prefix))
    cog_blobs = [
        blob for blob in blobs
        if blob.name.endswith('.tif') and not blob.name.endswith('/')
    ]
    
    print(f"Total COGs found: {len(cog_blobs)}")
    print(f"Sampling {min(num_samples, len(cog_blobs))} COGs...")
    print()
    
    # Sample evenly distributed COGs
    if len(cog_blobs) <= num_samples:
        sample_blobs = cog_blobs
    else:
        step = len(cog_blobs) // num_samples
        sample_blobs = [cog_blobs[i * step] for i in range(num_samples)]
    
    # Check dimensions
    results = []
    for i, blob in enumerate(sample_blobs, 1):
        cog_name = Path(blob.name).stem
        print(f"[{i}/{len(sample_blobs)}] Checking {cog_name}...")
        
        try:
            width, height = get_cog_dimensions(bucket_name, blob.name)
            chips_x, chips_y, total = calculate_max_chips(width, height)
            
            results.append({
                'name': cog_name,
                'width': width,
                'height': height,
                'chips_x': chips_x,
                'chips_y': chips_y,
                'total_chips': total
            })
            
            print(f"  Size: {width} × {height}")
            print(f"  Max chips: {chips_x} × {chips_y} = {total} chips")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            print()
    
    return results


def print_summary(results):
    """Print summary statistics."""
    if not results:
        print("No results to summarize")
        return
    
    widths = [r['width'] for r in results]
    heights = [r['height'] for r in results]
    total_chips = [r['total_chips'] for r in results]
    
    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print()
    
    print("Image Dimensions:")
    print(f"  Width:  {min(widths)} - {max(widths)} px (avg: {statistics.mean(widths):.0f})")
    print(f"  Height: {min(heights)} - {max(heights)} px (avg: {statistics.mean(heights):.0f})")
    print()
    
    print("Non-Overlapping 1024×1024 Chips:")
    print(f"  Min:  {min(total_chips)} chips per image")
    print(f"  Max:  {max(total_chips)} chips per image")
    print(f"  Avg:  {statistics.mean(total_chips):.1f} chips per image")
    print(f"  Median: {statistics.median(total_chips):.0f} chips per image")
    print()
    
    # Calculate total for all COGs
    num_cogs = 975  # Approximate total
    print(f"Extrapolation for ~{num_cogs} COGs:")
    print(f"  If 4 chips/image:  {num_cogs * 4:,} total chips")
    print(f"  If avg ({statistics.mean(total_chips):.0f}) chips/image:  {num_cogs * statistics.mean(total_chips):,.0f} total chips")
    print(f"  If max ({max(total_chips)}) chips/image:  {num_cogs * max(total_chips):,} total chips")
    print()
    
    print("Recommendations:")
    if min(total_chips) >= 16:
        print("  ✓ Images are large enough for 4+ chips per image")
        print("  ✓ Can safely extract 4-16 non-overlapping chips")
    elif min(total_chips) >= 4:
        print("  ✓ Most images support 4+ chips")
        print("  ⚠ Some smaller images may support fewer")
    else:
        print("  ⚠ Some images are small - may not fit 4 chips")
        print("  → Consider adaptive chip count per image")
    print()


def main():
    """Check COG dimensions and calculate chip capacity."""
    
    bucket_name = 'tumamoc-2023'
    cog_prefix = 'cogs/'
    num_samples = 20  # Sample 20 COGs
    
    print("=" * 70)
    print("COG Dimension Analysis")
    print("=" * 70)
    print(f"Bucket: gs://{bucket_name}/{cog_prefix}")
    print(f"Chip size: 1024 × 1024 pixels")
    print()
    
    # Sample COGs
    results = sample_cogs(bucket_name, cog_prefix, num_samples)
    
    # Print summary
    print_summary(results)
    
    print("=" * 70)


if __name__ == "__main__":
    main()

