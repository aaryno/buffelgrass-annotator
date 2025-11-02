#!/usr/bin/env python3
"""
Cloud Run Job for parallel COG conversion.

Each instance processes a subset of files from GCS.
Can run 100s of parallel instances for fast processing.

Environment Variables:
    TASK_INDEX: Cloud Run task index (0-based)
    TASK_COUNT: Total number of parallel tasks
    SOURCE_BUCKET: Source GCS bucket (default: tumamoc-2023)
    SOURCE_PREFIX: Source prefix (default: source-jpg/)
    COG_BUCKET: Destination bucket (default: tumamoc-2023)
    COG_PREFIX: Destination prefix (default: cogs/)
"""

import os
import sys
import tempfile
import subprocess
from google.cloud import storage
from pathlib import Path


def list_files_to_process(bucket_name, source_prefix, cog_prefix):
    """
    List files that need to be converted.
    Returns only files that don't already have corresponding COGs.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Get all source files
    source_blobs = list(bucket.list_blobs(prefix=source_prefix))
    source_files = [
        blob.name for blob in source_blobs 
        if not blob.name.endswith('/')
    ]
    
    # Get existing COGs
    cog_blobs = list(bucket.list_blobs(prefix=cog_prefix))
    existing_cogs = {
        Path(blob.name).stem: blob.name 
        for blob in cog_blobs 
        if not blob.name.endswith('/')
    }
    
    # Filter to files that need processing
    files_to_process = []
    for source_file in source_files:
        source_name = Path(source_file).stem
        if source_name not in existing_cogs:
            files_to_process.append(source_file)
    
    return files_to_process


def convert_file_to_cog(bucket_name, source_path, cog_path):
    """
    Convert a single JPEG to COG.
    
    Downloads source, converts with rio-cogeo, uploads result.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download source
        local_source = os.path.join(tmpdir, Path(source_path).name)
        source_blob = bucket.blob(source_path)
        source_blob.download_to_filename(local_source)
        
        # Convert to COG
        cog_name = Path(source_path).stem + '.tif'
        local_cog = os.path.join(tmpdir, cog_name)
        
        result = subprocess.run(
            [
                'rio', 'cogeo', 'create',
                local_source,
                local_cog,
                '--co', 'COMPRESS=JPEG',
                '--co', 'JPEG_QUALITY=85',
                '--co', 'TILED=YES',
                '--co', 'BLOCKXSIZE=512',
                '--co', 'BLOCKYSIZE=512',
                '--co', 'NUM_THREADS=ALL_CPUS',
                '--overview-level', '5'
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"COG conversion failed: {result.stderr}")
        
        # Upload COG
        cog_blob = bucket.blob(cog_path)
        cog_blob.upload_from_filename(local_cog, content_type='image/tiff')
        
        return os.path.getsize(local_cog)


def main():
    """
    Main processing loop for this Cloud Run task.
    
    Each task processes a subset of files based on TASK_INDEX.
    """
    # Get task info from environment
    task_index = int(os.getenv('CLOUD_RUN_TASK_INDEX', '0'))
    task_count = int(os.getenv('CLOUD_RUN_TASK_COUNT', '1'))
    
    # Get bucket config
    source_bucket = os.getenv('SOURCE_BUCKET', 'tumamoc-2023')
    source_prefix = os.getenv('SOURCE_PREFIX', 'source-jpg/')
    cog_bucket = os.getenv('COG_BUCKET', 'tumamoc-2023')
    cog_prefix = os.getenv('COG_PREFIX', 'cogs/')
    
    print(f"=" * 70)
    print(f"Cloud Run Task {task_index + 1}/{task_count}")
    print(f"=" * 70)
    print(f"Source: gs://{source_bucket}/{source_prefix}")
    print(f"Destination: gs://{cog_bucket}/{cog_prefix}")
    print()
    
    # List files to process
    print("Listing files to process...")
    all_files = list_files_to_process(source_bucket, source_prefix, cog_prefix)
    
    # Distribute files across tasks
    my_files = [f for i, f in enumerate(all_files) if i % task_count == task_index]
    
    print(f"Total files needing conversion: {len(all_files)}")
    print(f"This task will process: {len(my_files)} files")
    print()
    
    if not my_files:
        print("✓ No files to process")
        return 0
    
    # Process files
    success_count = 0
    failed = []
    
    for i, source_file in enumerate(my_files, 1):
        source_name = Path(source_file).stem
        cog_name = source_name + '.tif'
        cog_path = f"{cog_prefix}{cog_name}"
        
        print(f"[{i}/{len(my_files)}] {source_name}")
        
        try:
            cog_size = convert_file_to_cog(source_bucket, source_file, cog_path)
            print(f"  ✓ {cog_size / 1024 / 1024:.1f} MB")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed.append(source_name)
    
    # Summary
    print()
    print("=" * 70)
    print(f"Task {task_index + 1} Complete")
    print("=" * 70)
    print(f"Successful: {success_count}/{len(my_files)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed files:")
        for f in failed[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())


