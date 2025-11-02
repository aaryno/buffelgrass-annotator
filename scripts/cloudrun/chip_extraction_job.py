#!/usr/bin/env python3
"""
Cloud Run Job for parallel chip extraction from COGs.

Extracts 4 non-overlapping 1024x1024 chips from each COG and organizes them
into 10 folders for parallel annotation by multiple annotators.

Environment Variables:
    TASK_INDEX: Cloud Run task index (0-based)
    TASK_COUNT: Total number of parallel tasks
    SOURCE_BUCKET: Source GCS bucket (default: tumamoc-2023)
    SOURCE_PREFIX: Source prefix (default: cogs/)
    CHIPS_BUCKET: Destination bucket (default: tumamoc-2023)
    CHIPS_PREFIX: Destination prefix (default: training_chips/1024x1024/)
    CHIPS_PER_IMAGE: Number of chips per COG (default: 4)
    CHIP_SIZE: Chip size in pixels (default: 1024)
"""

import os
import sys
import tempfile
import hashlib
from pathlib import Path
from typing import List, Tuple

import rasterio
from rasterio.windows import Window
import numpy as np
from PIL import Image
from google.cloud import storage


def hash_filename_to_folder(filename: str, num_folders: int = 10) -> str:
    """
    Consistently hash filename to a folder number (01-10).
    
    Uses MD5 hash to ensure even distribution across folders.
    """
    hash_value = int(hashlib.md5(filename.encode()).hexdigest(), 16)
    folder_num = (hash_value % num_folders) + 1
    return f"{folder_num:02d}"


def generate_non_overlapping_grid_coords(
    image_width: int,
    image_height: int,
    chip_size: int,
    num_chips: int,
    margin: int = 10
) -> List[Tuple[int, int]]:
    """
    Generate non-overlapping chip coordinates using grid-based sampling.
    
    Divides image into grid and samples from different quadrants to ensure
    spatial diversity without overlap.
    
    Args:
        image_width: Width of source image
        image_height: Height of source image
        chip_size: Size of square chips
        num_chips: Number of chips to generate
        margin: Minimum distance from edges
        
    Returns:
        List of (ul_x, ul_y) tuples for upper-left corners
    """
    # Ensure chips fit in image
    if chip_size >= image_width - (2 * margin) or chip_size >= image_height - (2 * margin):
        raise ValueError(f"Chip size {chip_size} too large for image {image_width}x{image_height}")
    
    # Calculate usable dimensions
    usable_width = image_width - chip_size - (2 * margin)
    usable_height = image_height - chip_size - (2 * margin)
    
    # For 4 chips: sample from 4 quadrants (top-left, top-right, bottom-left, bottom-right)
    if num_chips == 4:
        grid_x = 2
        grid_y = 2
    elif num_chips <= 2:
        grid_x = num_chips
        grid_y = 1
    else:
        # For other counts, use square-ish grid
        grid_x = int(np.ceil(np.sqrt(num_chips)))
        grid_y = int(np.ceil(num_chips / grid_x))
    
    # Size of each grid cell
    cell_width = usable_width // grid_x
    cell_height = usable_height // grid_y
    
    # Generate one chip per grid cell
    coords = []
    chip_idx = 0
    
    for row in range(grid_y):
        for col in range(grid_x):
            if chip_idx >= num_chips:
                break
            
            # Sample from center of grid cell
            cell_ul_x = margin + (col * cell_width)
            cell_ul_y = margin + (row * cell_height)
            
            # Add some randomness within cell (25% of cell size)
            offset_range_x = cell_width // 4
            offset_range_y = cell_height // 4
            
            import random
            offset_x = random.randint(-offset_range_x, offset_range_x)
            offset_y = random.randint(-offset_range_y, offset_range_y)
            
            ul_x = max(margin, min(cell_ul_x + cell_width // 2 + offset_x, 
                                   image_width - chip_size - margin))
            ul_y = max(margin, min(cell_ul_y + cell_height // 2 + offset_y,
                                   image_height - chip_size - margin))
            
            coords.append((ul_x, ul_y))
            chip_idx += 1
    
    return coords


def extract_chip_from_cog(
    cog_gs_path: str,
    ul_x: int,
    ul_y: int,
    chip_size: int,
    output_path: str
) -> None:
    """
    Extract a chip from COG and save as PNG.
    
    Args:
        cog_gs_path: GCS path to COG (gs://bucket/path)
        ul_x: Upper-left X coordinate
        ul_y: Upper-left Y coordinate
        chip_size: Chip size in pixels
        output_path: Local path to save PNG
    """
    with rasterio.open(cog_gs_path) as src:
        # Read chip data using window
        window = Window(ul_x, ul_y, chip_size, chip_size)
        chip_data = src.read(window=window)
        
        # Convert from (bands, height, width) to (height, width, bands)
        img_data = np.transpose(chip_data, (1, 2, 0))
        
        # Create PIL Image and save as PNG
        img = Image.fromarray(img_data, mode='RGB')
        img.save(output_path, format='PNG')


def process_single_cog(
    bucket_name: str,
    cog_path: str,
    chips_prefix: str,
    num_chips: int,
    chip_size: int
) -> Tuple[int, List[str]]:
    """
    Process a single COG: extract chips and upload to appropriate folder.
    
    Returns:
        (success_count, failed_chips)
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Determine folder number from filename hash
    cog_name = Path(cog_path).stem
    folder_num = hash_filename_to_folder(cog_name)
    
    # Get COG dimensions
    cog_gs_path = f"gs://{bucket_name}/{cog_path}"
    
    with rasterio.open(cog_gs_path) as src:
        width, height = src.width, src.height
    
    print(f"  Image size: {width}x{height}")
    print(f"  Folder: {folder_num}")
    
    # Generate non-overlapping chip coordinates
    try:
        chip_coords = generate_non_overlapping_grid_coords(
            width, height, chip_size, num_chips
        )
    except ValueError as e:
        print(f"  ✗ Cannot generate chips: {e}")
        return 0, [f"all_{cog_name}"]
    
    # Extract and upload chips
    success_count = 0
    failed_chips = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (ul_x, ul_y) in enumerate(chip_coords):
            # Name format: A_{source_name}_{chipnum}.png
            chip_name = f"A_{cog_name}_{i+1:02d}.png"
            local_chip_path = os.path.join(tmpdir, chip_name)
            
            try:
                # Extract chip
                extract_chip_from_cog(
                    cog_gs_path, ul_x, ul_y, chip_size, local_chip_path
                )
                
                # Upload to appropriate folder
                gcs_chip_path = f"{chips_prefix}{folder_num}/{chip_name}"
                chip_blob = bucket.blob(gcs_chip_path)
                chip_blob.upload_from_filename(local_chip_path, content_type='image/png')
                
                file_size_kb = os.path.getsize(local_chip_path) / 1024
                print(f"    ✓ Chip {i+1}: {chip_name} ({file_size_kb:.1f} KB)")
                success_count += 1
                
            except Exception as e:
                print(f"    ✗ Chip {i+1} failed: {e}")
                failed_chips.append(chip_name)
    
    return success_count, failed_chips


def list_cogs_to_process(bucket_name: str, source_prefix: str) -> List[str]:
    """
    List all COG files in source prefix.
    
    Returns list of blob paths.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    blobs = list(bucket.list_blobs(prefix=source_prefix))
    cog_files = [
        blob.name for blob in blobs
        if blob.name.endswith('.tif') and not blob.name.endswith('/')
    ]
    
    return cog_files


def main():
    """
    Main processing loop for chip extraction Cloud Run task.
    
    Each task processes a subset of COGs based on TASK_INDEX.
    """
    # Get task info from environment
    task_index = int(os.getenv('CLOUD_RUN_TASK_INDEX', '0'))
    task_count = int(os.getenv('CLOUD_RUN_TASK_COUNT', '1'))
    
    # Get configuration
    source_bucket = os.getenv('SOURCE_BUCKET', 'tumamoc-2023')
    source_prefix = os.getenv('SOURCE_PREFIX', 'cogs/')
    chips_bucket = os.getenv('CHIPS_BUCKET', 'tumamoc-2023')
    chips_prefix = os.getenv('CHIPS_PREFIX', 'training_chips/1024x1024/')
    num_chips = int(os.getenv('CHIPS_PER_IMAGE', '4'))
    chip_size = int(os.getenv('CHIP_SIZE', '1024'))
    
    print("=" * 70)
    print(f"Chip Extraction - Task {task_index + 1}/{task_count}")
    print("=" * 70)
    print(f"Source: gs://{source_bucket}/{source_prefix}")
    print(f"Destination: gs://{chips_bucket}/{chips_prefix}{{01-10}}/")
    print(f"Chips per image: {num_chips}")
    print(f"Chip size: {chip_size}x{chip_size}")
    print()
    
    # List COGs to process
    print("Listing COGs to process...")
    all_cogs = list_cogs_to_process(source_bucket, source_prefix)
    
    # Distribute COGs across tasks
    my_cogs = [cog for i, cog in enumerate(all_cogs) if i % task_count == task_index]
    
    print(f"Total COGs: {len(all_cogs)}")
    print(f"This task will process: {len(my_cogs)} COGs")
    print(f"Expected chips: {len(my_cogs) * num_chips}")
    print()
    
    if not my_cogs:
        print("✓ No COGs to process")
        return 0
    
    # Process each COG
    total_chips = 0
    failed_cogs = []
    
    for i, cog_path in enumerate(my_cogs, 1):
        cog_name = Path(cog_path).stem
        print(f"[{i}/{len(my_cogs)}] {cog_name}")
        
        try:
            success_count, failed_chips = process_single_cog(
                source_bucket,
                cog_path,
                chips_prefix,
                num_chips,
                chip_size
            )
            
            total_chips += success_count
            
            if failed_chips:
                failed_cogs.append((cog_name, failed_chips))
                
        except Exception as e:
            print(f"  ✗ Failed to process COG: {e}")
            failed_cogs.append((cog_name, ["all"]))
    
    # Summary
    print()
    print("=" * 70)
    print(f"Task {task_index + 1} Complete")
    print("=" * 70)
    print(f"COGs processed: {len(my_cogs)}")
    print(f"Chips extracted: {total_chips}")
    print(f"Failed COGs: {len(failed_cogs)}")
    
    if failed_cogs:
        print("\nFailed COGs:")
        for cog_name, chips in failed_cogs[:10]:
            print(f"  - {cog_name}: {len(chips)} chips failed")
        if len(failed_cogs) > 10:
            print(f"  ... and {len(failed_cogs) - 10} more")
    
    return 0 if not failed_cogs else 1


if __name__ == "__main__":
    sys.exit(main())


