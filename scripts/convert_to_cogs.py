#!/usr/bin/env python3
"""
Convert source JPEGs to Cloud-Optimized GeoTIFFs (COGs) in GCS.

This script:
1. Lists all files in gs://tumamoc-2023/source-jpg/
2. For each file, checks if COG already exists in gs://tumamoc-2023/cogs/
3. Downloads source, converts to COG, uploads to destination
4. Tracks progress and handles errors

Usage:
    python convert_to_cogs.py [--overwrite] [--max-files N]
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from google.cloud import storage
import subprocess

# Configuration
GCS_BUCKET = "tumamoc-2023"
SOURCE_PREFIX = "source-jpg/"
COG_PREFIX = "cogs/"


def check_dependencies():
    """Check if required tools are installed."""
    try:
        result = subprocess.run(
            ['rio', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("❌ rasterio CLI (rio) not found")
            print("\nInstall with:")
            print("  pip install rasterio rio-cogeo")
            return False
        print(f"✓ rasterio: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ rasterio CLI (rio) not found")
        print("\nInstall with:")
        print("  pip install rasterio rio-cogeo")
        return False


def list_source_files(bucket_name, prefix):
    """List all source files in GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    files = []
    for blob in blobs:
        # Skip directories
        if blob.name.endswith('/'):
            continue
        files.append({
            'name': blob.name.replace(prefix, ''),
            'source_path': blob.name,
            'size': blob.size
        })
    
    return files


def cog_exists(bucket_name, cog_path):
    """Check if COG already exists in GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(cog_path)
    return blob.exists()


def convert_to_cog(source_path, dest_path):
    """
    Convert JPEG/TIFF to Cloud-Optimized GeoTIFF using rio cogeo.
    
    Args:
        source_path: Local path to source file
        dest_path: Local path for output COG
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use rio cogeo create command
        result = subprocess.run(
            [
                'rio', 'cogeo', 'create',
                source_path,
                dest_path,
                '--co', 'COMPRESS=JPEG',
                '--co', 'JPEG_QUALITY=85',
                '--co', 'TILED=YES',
                '--co', 'BLOCKXSIZE=512',
                '--co', 'BLOCKYSIZE=512',
                '--co', 'NUM_THREADS=ALL_CPUS',
                '--overview-level', '5'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"    Conversion error: {e.stderr[:200]}")
        return False
    except Exception as e:
        print(f"    Conversion error: {e}")
        return False


def process_file(file_info, bucket_name, overwrite=False):
    """
    Process a single file: download, convert to COG, upload.
    
    Args:
        file_info: Dict with 'name', 'source_path', 'size'
        bucket_name: GCS bucket name
        overwrite: If True, overwrite existing COGs
    
    Returns:
        True if successful, False otherwise
    """
    source_name = file_info['name']
    source_path = file_info['source_path']
    
    # Determine COG filename (change extension to .tif)
    cog_name = Path(source_name).stem + '.tif'
    cog_path = f"{COG_PREFIX}{cog_name}"
    
    # Check if COG already exists
    if not overwrite and cog_exists(bucket_name, cog_path):
        print(f"  ⊘ Already exists: {cog_name}")
        return True
    
    # Create temp directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        local_source = os.path.join(tmpdir, source_name)
        local_cog = os.path.join(tmpdir, cog_name)
        
        try:
            # Download source file
            print(f"  ↓ Downloading...")
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            blob = bucket.blob(source_path)
            blob.download_to_filename(local_source)
            
            # Convert to COG
            print(f"  ⚙ Converting to COG...")
            if not convert_to_cog(local_source, local_cog):
                return False
            
            # Upload COG
            print(f"  ↑ Uploading...")
            cog_blob = bucket.blob(cog_path)
            cog_blob.upload_from_filename(local_cog, content_type='image/tiff')
            
            # Get final size
            cog_size = os.path.getsize(local_cog)
            compression_ratio = (1 - cog_size / file_info['size']) * 100
            
            print(f"  ✓ Complete: {cog_name}")
            print(f"    Size: {format_size(file_info['size'])} → {format_size(cog_size)} ({compression_ratio:+.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False


def format_size(bytes_size):
    """Format bytes to human-readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Convert source JPEGs to COGs in GCS'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing COGs'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to process (for testing)'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("JPEG → COG CONVERSION")
    print("=" * 70)
    print(f"Source: gs://{GCS_BUCKET}/{SOURCE_PREFIX}")
    print(f"Destination: gs://{GCS_BUCKET}/{COG_PREFIX}")
    print(f"Overwrite: {args.overwrite}")
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print()
    
    # List source files
    print("Scanning source files...")
    files = list_source_files(GCS_BUCKET, SOURCE_PREFIX)
    
    if not files:
        print("❌ No source files found")
        sys.exit(1)
    
    if args.max_files:
        files = files[:args.max_files]
        print(f"Processing first {len(files)} files (--max-files={args.max_files})")
    
    total_size = sum(f['size'] for f in files)
    print(f"Found {len(files)} files ({format_size(total_size)})")
    print()
    
    # Process files
    print("=" * 70)
    print("Processing files...")
    print("=" * 70)
    
    success_count = 0
    failed = []
    
    for i, file_info in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {file_info['name']}")
        print(f"  Size: {format_size(file_info['size'])}")
        
        if process_file(file_info, GCS_BUCKET, args.overwrite):
            success_count += 1
        else:
            failed.append(file_info['name'])
    
    # Summary
    print()
    print("=" * 70)
    print("CONVERSION COMPLETE")
    print("=" * 70)
    print(f"Successful: {success_count}/{len(files)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed files:")
        for f in failed:
            print(f"  - {f}")
    
    print()
    print(f"COGs available at: gs://{GCS_BUCKET}/{COG_PREFIX}")
    print()


if __name__ == "__main__":
    main()


