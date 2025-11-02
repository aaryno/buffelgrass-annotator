#!/usr/bin/env python3
"""
Count files in Dropbox folder and convert to COG with progress tracking.

Usage:
    python count_and_convert_dropbox.py --list-only  # Just count files
    python count_and_convert_dropbox.py              # Convert all files
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime
from google.cloud import storage
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import json

# Dropbox shared folder URLs (replace with your actual URLs)
DROPBOX_FOLDERS = {
    "tumamoc_source": {
        "url": "https://www.dropbox.com/scl/fo/cxb7mkl80f8ux9sfpfoty/AGhAKqDZ0MNjE4V0ZgrlI6M?rlkey=fu5b5hbr6jo6nn7zsknky4w60&e=1&st=blcns2qb&dl=0",
        "description": "Tumamoc Hill source JPEGs (Feb 2023)"
    },
    "tumamoc_mosaic": {
        "url": "https://www.dropbox.com/scl/fo/pem5nivwv9lgk6rgnc6c4/AAeaBOUbO4qgbshJguxBHZg?rlkey=zkfxodsst7x4ucsoq255pp0mw&e=1&dl=0",
        "description": "Tumamoc Hill orthorectified mosaic (Feb 2023)"
    },
    "sabino_canyon": {
        "url": "https://www.dropbox.com/scl/fo/fuvghz49888ghi2wgpfbg/AAZErLk0UZ27p0ini0Skei0?rlkey=v1kelsdn5a3yv1b723a8ytpwz&e=1&st=7xaebghy&dl=0",
        "description": "Sabino Canyon JPEG2000 series (2024)"
    }
}

GCS_BUCKET = "tumamoc-2023"
PROGRESS_FILE = "conversion_progress.json"


def get_dropbox_folder_metadata(shared_link):
    """
    Get file list from Dropbox shared folder.
    
    Note: This requires Dropbox API access. For manual use:
    1. Visit the Dropbox link in browser
    2. Click "Download" -> "Direct download" for each file
    3. Or use Dropbox desktop app to sync folder
    
    This function is a placeholder - you'll need to manually list files
    or use Dropbox API with authentication.
    """
    print("⚠️  Cannot automatically list Dropbox files without API access")
    print("   Please manually list files or download folder first")
    return []


def scan_local_directory(directory):
    """Scan local directory for image files."""
    image_extensions = {'.jpg', '.jpeg', '.jp2', '.tif', '.tiff', '.png'}
    files = []
    
    directory = Path(directory)
    if not directory.exists():
        return files
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            files.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'extension': file_path.suffix.lower()
            })
    
    return files


def load_progress():
    """Load conversion progress from file."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'converted': [],
        'failed': [],
        'total': 0,
        'started': None,
        'last_updated': None
    }


def save_progress(progress):
    """Save conversion progress to file."""
    progress['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def convert_to_cog(input_path, output_path, quality=90):
    """Convert image to Cloud-Optimized GeoTIFF."""
    profile = cog_profiles.get("jpeg")
    profile.update({
        "QUALITY": quality,
        "TILED": True,
        "BLOCKXSIZE": 512,
        "BLOCKYSIZE": 512,
        "COMPRESS": "JPEG"
    })
    
    cog_translate(
        str(input_path),
        str(output_path),
        profile,
        in_memory=False,
        overview_level=5,
        overview_resampling="bilinear"
    )


def upload_to_gcs(local_path, bucket_name, blob_name):
    """Upload file to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.upload_from_filename(str(local_path))
    
    return f"gs://{bucket_name}/{blob_name}"


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def print_summary(files):
    """Print summary of files found."""
    print("\n" + "=" * 70)
    print("FILE INVENTORY")
    print("=" * 70)
    
    total_size = sum(f['size'] for f in files)
    
    print(f"\nTotal files found: {len(files)}")
    print(f"Total size: {format_size(total_size)}")
    
    # Group by extension
    by_extension = {}
    for f in files:
        ext = f['extension']
        if ext not in by_extension:
            by_extension[ext] = {'count': 0, 'size': 0}
        by_extension[ext]['count'] += 1
        by_extension[ext]['size'] += f['size']
    
    print("\nBreakdown by type:")
    for ext, info in sorted(by_extension.items()):
        print(f"  {ext:8s}: {info['count']:3d} files, {format_size(info['size']):>10s}")
    
    print("\n" + "=" * 70)


def convert_directory(source_dir, dry_run=False):
    """
    Convert all images in directory to COG and upload to GCS.
    
    Args:
        source_dir: Path to directory containing source images
        dry_run: If True, only list files without converting
    """
    print(f"\nScanning directory: {source_dir}")
    files = scan_local_directory(source_dir)
    
    if not files:
        print(f"❌ No image files found in {source_dir}")
        return
    
    print_summary(files)
    
    if dry_run:
        print("\n✓ Dry run complete. Use without --list-only to start conversion.")
        return
    
    # Load progress
    progress = load_progress()
    if progress['started'] is None:
        progress['started'] = datetime.now().isoformat()
        progress['total'] = len(files)
    
    # Filter out already converted files
    converted_names = set(progress['converted'])
    files_to_convert = [f for f in files if f['name'] not in converted_names]
    
    if not files_to_convert:
        print("\n✓ All files already converted!")
        return
    
    print(f"\n{len(files_to_convert)} files remaining to convert")
    print(f"({len(converted_names)} already completed)\n")
    
    # Convert each file
    temp_dir = Path("/tmp/cog_conversion")
    temp_dir.mkdir(exist_ok=True)
    
    for i, file_info in enumerate(files_to_convert, 1):
        file_path = Path(file_info['path'])
        file_name = file_info['name']
        
        print(f"\n[{i + len(converted_names)}/{len(files)}] {file_name}")
        print(f"  Size: {format_size(file_info['size'])}")
        
        try:
            # Generate output filename
            output_name = file_path.stem + "_cog.tif"
            output_path = temp_dir / output_name
            
            # Convert to COG
            print("  Converting to COG...")
            convert_to_cog(file_path, output_path)
            
            # Upload to GCS
            print("  Uploading to GCS...")
            gcs_path = f"source_cogs/{output_name}"
            gcs_url = upload_to_gcs(output_path, GCS_BUCKET, gcs_path)
            
            # Cleanup temp file
            output_path.unlink()
            
            # Update progress
            progress['converted'].append(file_name)
            save_progress(progress)
            
            print(f"  ✓ Complete: {gcs_url}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            progress['failed'].append({
                'file': file_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            save_progress(progress)
    
    # Final summary
    print("\n" + "=" * 70)
    print("CONVERSION COMPLETE")
    print("=" * 70)
    print(f"Total files: {progress['total']}")
    print(f"Converted: {len(progress['converted'])}")
    print(f"Failed: {len(progress['failed'])}")
    
    if progress['failed']:
        print("\nFailed files:")
        for failure in progress['failed']:
            print(f"  - {failure['file']}: {failure['error']}")
    
    print(f"\nAll converted files available at: gs://{GCS_BUCKET}/source_cogs/")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Count and convert Dropbox images to COG format"
    )
    parser.add_argument(
        '--source-dir',
        type=str,
        help='Local directory containing downloaded Dropbox files',
        required=True
    )
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list files without converting'
    )
    parser.add_argument(
        '--reset-progress',
        action='store_true',
        help='Reset progress tracking and start over'
    )
    
    args = parser.parse_args()
    
    if args.reset_progress:
        if Path(PROGRESS_FILE).exists():
            Path(PROGRESS_FILE).unlink()
            print("✓ Progress reset")
    
    convert_directory(args.source_dir, dry_run=args.list_only)


if __name__ == "__main__":
    main()

