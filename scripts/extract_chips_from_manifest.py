#!/usr/bin/env python3
"""
Extract chip images from COGs based on chip manifest.

Usage:
    python extract_chips_from_manifest.py --bin aa --count 500 --output-dir chips_aa/
    
This will:
1. Read chip-manifest.csv
2. Filter chips from the specified bin
3. Extract the actual chip images from source COGs
4. Save them with the manifest-specified filenames
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict

import rasterio
from rasterio.windows import Window
from PIL import Image
import numpy as np
from google.cloud import storage


def get_gcloud_access_token(config_name='asdm'):
    """Get access token from gcloud configuration."""
    import subprocess
    
    # Try common gcloud paths
    gcloud_paths = [
        '/opt/homebrew/bin/gcloud',
        '/usr/local/bin/gcloud',
        '/opt/homebrew/share/google-cloud-sdk/bin/gcloud',
        'gcloud'  # Try PATH
    ]
    
    gcloud_cmd = None
    for path in gcloud_paths:
        if os.path.exists(path) or path == 'gcloud':
            gcloud_cmd = path
            break
    
    if not gcloud_cmd:
        raise FileNotFoundError("gcloud command not found")
    
    try:
        result = subprocess.run(
            [gcloud_cmd, '--configuration', config_name, 'auth', 'print-access-token'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get gcloud access token: {e.stderr}")


def setup_gcs_credentials():
    """Set up GCS credentials for rasterio."""
    os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
    os.environ['CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE'] = 'NO'
    
    try:
        token = get_gcloud_access_token('asdm')
        os.environ['GS_OAUTH2_TOKEN'] = token
        print("✓ GCS credentials configured for rasterio")
    except Exception as e:
        print(f"Warning: Could not set up GCS token: {e}")
        print("Using default credentials...")


def read_manifest(manifest_path: str, bin_name: str = None, count: int = None) -> List[Dict]:
    """Read chip manifest and filter by bin."""
    chips = []
    
    with open(manifest_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract bin from chip_path (e.g., "aa/aa-sn-cap-29792.png" -> "aa")
            chip_bin = row['chip_path'].split('/')[0]
            
            if bin_name is None or chip_bin == bin_name:
                chips.append(row)
                
                if count and len(chips) >= count:
                    break
    
    return chips


def extract_chip(cog_path: str, ulx: int, uly: int, width: int, height: int) -> np.ndarray:
    """Extract a chip from a COG file."""
    with rasterio.open(cog_path) as src:
        # Read the window
        window = Window(ulx, uly, width, height)
        chip_data = src.read(window=window)
        
        # Convert from (bands, height, width) to (height, width, bands)
        if chip_data.shape[0] in [3, 4]:  # RGB or RGBA
            chip_data = np.transpose(chip_data, (1, 2, 0))
        
        return chip_data


def save_chip(chip_data: np.ndarray, output_path: str):
    """Save chip as PNG."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to PIL Image and save
    if chip_data.dtype == np.uint16:
        # Scale 16-bit to 8-bit
        chip_data = (chip_data / 256).astype(np.uint8)
    
    img = Image.fromarray(chip_data)
    img.save(output_path, 'PNG')


def main():
    parser = argparse.ArgumentParser(description='Extract chips from COGs based on manifest')
    parser.add_argument('--manifest', default='chip-manifest.csv', help='Path to chip manifest CSV')
    parser.add_argument('--bin', required=True, help='Bin to extract chips from (e.g., aa, rf, xy)')
    parser.add_argument('--count', type=int, help='Number of chips to extract (default: all)')
    parser.add_argument('--output-dir', required=True, help='Output directory for chips')
    parser.add_argument('--bucket', default='tumamoc-2023', help='GCS bucket name')
    parser.add_argument('--source-prefix', default='cogs/', help='Prefix for source COGs in bucket')
    
    args = parser.parse_args()
    
    # Setup GCS credentials
    setup_gcs_credentials()
    
    print(f"\n{'='*70}")
    print(f"Extracting Chips from Bin: {args.bin}")
    print(f"{'='*70}\n")
    
    # Read manifest
    print(f"Reading manifest: {args.manifest}")
    chips = read_manifest(args.manifest, args.bin, args.count)
    print(f"Found {len(chips)} chips in bin '{args.bin}'")
    
    if len(chips) == 0:
        print(f"No chips found for bin '{args.bin}'")
        return
    
    # Extract chips
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    error_count = 0
    
    for i, chip in enumerate(chips, 1):
        chip_path = chip['chip_path']
        source_image = chip['source_image']
        ulx = int(chip['ulx'])
        uly = int(chip['uly'])
        width = int(chip['width'])
        height = int(chip['height'])
        
        # Construct COG path
        cog_path = f"/vsigs/{args.bucket}/{args.source_prefix}{source_image}.tif"
        
        # Output path (flatten directory structure)
        output_path = output_dir / Path(chip_path).name
        
        try:
            print(f"[{i}/{len(chips)}] Extracting {output_path.name}...", end=' ')
            
            # Extract and save chip
            chip_data = extract_chip(cog_path, ulx, uly, width, height)
            save_chip(chip_data, str(output_path))
            
            print("✓")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Error: {e}")
            error_count += 1
    
    print(f"\n{'='*70}")
    print(f"Extraction Complete")
    print(f"{'='*70}")
    print(f"Success: {success_count}")
    print(f"Errors:  {error_count}")
    print(f"Output:  {output_dir}/")
    print(f"\nTotal size: {sum(f.stat().st_size for f in output_dir.glob('*.png')) / (1024*1024):.1f} MB")


if __name__ == '__main__':
    main()


