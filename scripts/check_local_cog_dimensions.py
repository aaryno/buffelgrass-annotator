#!/usr/bin/env python3
"""
Check dimensions of downloaded COG files.
Simpler approach that doesn't require GCS authentication for rasterio.
"""

import sys
import rasterio
from pathlib import Path


def calculate_max_chips(width, height, chip_size=1024, margin=10):
    """Calculate maximum non-overlapping chips."""
    usable_width = width - (2 * margin)
    usable_height = height - (2 * margin)
    
    num_chips_x = usable_width // chip_size
    num_chips_y = usable_height // chip_size
    total_chips = num_chips_x * num_chips_y
    
    return num_chips_x, num_chips_y, total_chips


def check_cog(filepath):
    """Check a single COG file."""
    with rasterio.open(filepath) as src:
        width = src.width
        height = src.height
        bands = src.count
        dtype = src.dtypes[0]
        
        chips_x, chips_y, total = calculate_max_chips(width, height)
        
        return {
            'width': width,
            'height': height,
            'bands': bands,
            'dtype': dtype,
            'chips_x': chips_x,
            'chips_y': chips_y,
            'total_chips': total
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_local_cog_dimensions.py <path_to_cog.tif>")
        sys.exit(1)
    
    cog_path = sys.argv[1]
    
    if not Path(cog_path).exists():
        print(f"Error: File not found: {cog_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("COG Dimension Analysis")
    print("=" * 70)
    print(f"File: {cog_path}")
    print()
    
    result = check_cog(cog_path)
    
    print(f"Image dimensions: {result['width']} × {result['height']} pixels")
    print(f"Bands: {result['bands']}")
    print(f"Data type: {result['dtype']}")
    print()
    
    print("Non-overlapping 1024×1024 chips:")
    print(f"  Grid: {result['chips_x']} × {result['chips_y']}")
    print(f"  Total: {result['total_chips']} chips")
    print()
    
    # Extrapolate for ~976 COGs
    num_cogs = 976
    print(f"Extrapolation for ~{num_cogs} COGs:")
    print(f"  If 4 chips/image:  {num_cogs * 4:,} total chips")
    print(f"  If {result['total_chips']} chips/image:  {num_cogs * result['total_chips']:,} total chips")
    print()
    
    # Calculate coverage
    chip_coverage = (result['total_chips'] * 1024 * 1024) / (result['width'] * result['height'])
    print(f"Coverage: {chip_coverage * 100:.1f}% of image area with non-overlapping chips")
    print()
    
    print("=" * 70)


if __name__ == "__main__":
    main()


