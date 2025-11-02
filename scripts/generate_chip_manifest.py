#!/usr/bin/env python3
"""
Generate manifest of all possible non-overlapping chip windows.

Pre-computes a 6×5 grid (30 chips) per source COG and assigns each
to one of 625 bins (AA through YY) for flexible sampling later.

Output CSV format:
chip_path,source_image,ulx,uly,width,height

Example:
rf/rf-cap-30704.png,cap-30704,1323,712,1024,1024
"""

import sys
import os
import csv
import hashlib
import rasterio
from pathlib import Path
from typing import List, Tuple, Dict


def generate_bin_labels(num_bins=625):
    """
    Generate 625 bin labels: AA through YY (25×25).
    
    Returns list of 2-letter combinations.
    """
    # For 625 bins, use A-Y (25 letters) for both positions
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
    """Hash a value to a bin index (0 to num_bins-1)."""
    hash_value = int(hashlib.md5(value.encode()).hexdigest(), 16)
    return hash_value % num_bins


def compute_chip_grid(width: int, height: int, chip_size: int = 1024, 
                      grid_x: int = 6, grid_y: int = 5, margin: int = 10) -> List[Tuple[int, int]]:
    """
    Compute non-overlapping grid of chip windows.
    
    Args:
        width: Image width
        height: Image height
        chip_size: Chip size (1024×1024)
        grid_x: Number of chips horizontally (6)
        grid_y: Number of chips vertically (5)
        margin: Edge margin to avoid borders
        
    Returns:
        List of (ulx, uly) tuples for upper-left corners
        Returns empty list if image too small
    """
    # Calculate required dimensions
    required_width = (grid_x * chip_size) + (2 * margin)
    required_height = (grid_y * chip_size) + (2 * margin)
    
    if width < required_width or height < required_height:
        return []  # Image too small for 6×5 grid
    
    # Calculate usable area
    usable_width = width - (2 * margin)
    usable_height = height - (2 * margin)
    
    # Calculate spacing between chips
    spacing_x = (usable_width - (grid_x * chip_size)) // (grid_x - 1) if grid_x > 1 else 0
    spacing_y = (usable_height - (grid_y * chip_size)) // (grid_y - 1) if grid_y > 1 else 0
    
    # Generate chip coordinates
    chips = []
    for row in range(grid_y):
        for col in range(grid_x):
            ulx = margin + (col * (chip_size + spacing_x))
            uly = margin + (row * (chip_size + spacing_y))
            
            # Ensure chip stays within bounds
            if ulx + chip_size <= width - margin and uly + chip_size <= height - margin:
                chips.append((ulx, uly))
    
    return chips


def process_single_image(image_path: str, image_name: str, bin_labels: List[str], 
                        chip_size: int = 1024) -> List[Dict]:
    """
    Process a single image and generate chip manifest entries.
    
    Args:
        image_path: Path to COG (local or gs://)
        image_name: Source image name (without extension)
        bin_labels: List of 625 bin labels
        chip_size: Chip size
        
    Returns:
        List of dicts with chip metadata
    """
    # Read image metadata
    with rasterio.open(image_path) as src:
        width = src.width
        height = src.height
    
    print(f"  Image: {image_name}")
    print(f"  Dimensions: {width} × {height}")
    
    # Compute chip grid
    chip_coords = compute_chip_grid(width, height, chip_size, grid_x=6, grid_y=5)
    
    if not chip_coords:
        print(f"  ✗ Image too small for 6×5 grid")
        return []
    
    print(f"  Chips: {len(chip_coords)}")
    
    # Generate manifest entries
    entries = []
    for idx, (ulx, uly) in enumerate(chip_coords):
        # Assign to bin using hash of image+index
        bin_key = f"{image_name}_{idx}"
        bin_idx = hash_to_bin(bin_key, len(bin_labels))
        bin_label = bin_labels[bin_idx].lower()
        
        # Add random 2-letter token for additional randomness
        random_token = generate_random_token()
        
        # Generate chip filename
        chip_filename = f"{bin_label}-{random_token}-{image_name}.png"
        chip_path = f"{bin_label}/{chip_filename}"
        
        entry = {
            'chip_path': chip_path,
            'source_image': image_name,
            'ulx': ulx,
            'uly': uly,
            'width': chip_size,
            'height': chip_size,
            'bin': bin_label
        }
        entries.append(entry)
    
    return entries


def print_csv_output(entries: List[Dict]):
    """Print entries in CSV format."""
    if not entries:
        print("No entries to output")
        return
    
    print("\nCSV Output:")
    print("=" * 80)
    print("chip_path,source_image,ulx,uly,width,height")
    for entry in entries:
        print(f"{entry['chip_path']},{entry['source_image']},{entry['ulx']},{entry['uly']},{entry['width']},{entry['height']}")


def print_statistics(entries: List[Dict]):
    """Print statistics about the manifest."""
    from collections import Counter
    
    if not entries:
        return
    
    bins = [e['bin'] for e in entries]
    bin_counts = Counter(bins)
    
    print("\n" + "=" * 80)
    print("Statistics")
    print("=" * 80)
    print(f"Total chips: {len(entries)}")
    print(f"Unique bins used: {len(bin_counts)}")
    print(f"Min chips per bin: {min(bin_counts.values())}")
    print(f"Max chips per bin: {max(bin_counts.values())}")
    print(f"Avg chips per bin: {len(entries) / len(bin_counts):.1f}")
    print()
    print("Sample bin distribution:")
    for bin_label in sorted(bin_counts.keys())[:10]:
        print(f"  {bin_label}: {bin_counts[bin_label]} chips")
    if len(bin_counts) > 10:
        print(f"  ... and {len(bin_counts) - 10} more bins")


def main():
    """Simulate manifest generation with one test image."""
    
    if len(sys.argv) < 2:
        print("Usage: python generate_chip_manifest.py <path_to_test_cog.tif>")
        print("\nSimulation mode - testing with sample dimensions")
        # Simulate with typical dimensions
        width, height = 10000, 8000
        image_name = "cap-30704"
        print(f"\nSimulating with {image_name}: {width}×{height}")
        
        # Generate bin labels
        bin_labels = generate_bin_labels(625)
        print(f"Generated {len(bin_labels)} bin labels (AA-YY)")
        print(f"Sample bins: {bin_labels[:5]} ... {bin_labels[-5:]}")
        print()
        
        # Compute chip grid
        chip_coords = compute_chip_grid(width, height)
        print(f"Computed {len(chip_coords)} chip windows")
        print()
        
        # Generate manifest entries (simulation)
        entries = []
        for idx, (ulx, uly) in enumerate(chip_coords):
            bin_key = f"{image_name}_{idx}"
            bin_idx = hash_to_bin(bin_key, len(bin_labels))
            bin_label = bin_labels[bin_idx].lower()
            
            random_token = generate_random_token()
            chip_filename = f"{bin_label}-{random_token}-{image_name}.png"
            chip_path = f"{bin_label}/{chip_filename}"
            
            entry = {
                'chip_path': chip_path,
                'source_image': image_name,
                'ulx': ulx,
                'uly': uly,
                'width': 1024,
                'height': 1024,
                'bin': bin_label
            }
            entries.append(entry)
        
        # Print output
        print_csv_output(entries)
        print_statistics(entries)
        
        print("\n" + "=" * 80)
        print("To run with actual COG:")
        print("  python generate_chip_manifest.py <path_to_cog.tif>")
        print("\nFor full manifest generation:")
        print("  Deploy as Cloud Run job to process all ~976 COGs")
        print("=" * 80)
        
        return
    
    # Process actual COG file
    cog_path = sys.argv[1]
    
    if not os.path.exists(cog_path) and not cog_path.startswith('gs://'):
        print(f"Error: File not found: {cog_path}")
        sys.exit(1)
    
    image_name = Path(cog_path).stem
    
    print("=" * 80)
    print("Chip Manifest Generator - Single Image Test")
    print("=" * 80)
    print()
    
    # Generate bin labels
    bin_labels = generate_bin_labels(625)
    print(f"Generated {len(bin_labels)} bin labels")
    print()
    
    # Process image
    entries = process_single_image(cog_path, image_name, bin_labels)
    
    if entries:
        print_csv_output(entries)
        print_statistics(entries)
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

