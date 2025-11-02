#!/usr/bin/env python3
"""
Extract provenance information from chip filenames.

Chip naming format: {source_image}_{ulx}_{uly}_{width}_{height}.png
Example: cap-29792_6666_4691_1024_1024.png

This allows you to:
- Identify which source image a chip came from
- Locate the exact coordinates within the source image
- Recreate the chip from the original COG if needed
"""

import argparse
from pathlib import Path
import re

def parse_chip_filename(filename: str) -> dict:
    """
    Parse chip filename to extract provenance information.
    
    Args:
        filename: Chip filename (e.g., 'cap-29792_6666_4691_1024_1024.png')
        
    Returns:
        Dictionary with source_image, ulx, uly, width, height
    """
    # Remove extension
    stem = Path(filename).stem
    
    # Pattern: {name}_{ulx}_{uly}_{width}_{height}
    # Name may contain hyphens
    pattern = r'^(.+)_(\d+)_(\d+)_(\d+)_(\d+)$'
    match = re.match(pattern, stem)
    
    if not match:
        return None
    
    return {
        'source_image': match.group(1),
        'upper_left_x': int(match.group(2)),
        'upper_left_y': int(match.group(3)),
        'width': int(match.group(4)),
        'height': int(match.group(5)),
        'lower_right_x': int(match.group(2)) + int(match.group(4)),
        'lower_right_y': int(match.group(3)) + int(match.group(5)),
    }

def main():
    parser = argparse.ArgumentParser(
        description="Extract provenance information from chip filenames",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get info for a single chip
  python chip_info.py data/training_chips/34/cap-29792_6666_4691_1024_1024.png
  
  # Process multiple chips
  find data/training_chips -name "*.png" | xargs -n1 python chip_info.py
        """
    )
    parser.add_argument('chip_file', type=str, help='Path to chip file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    info = parse_chip_filename(args.chip_file)
    
    if not info:
        print(f"❌ Could not parse filename: {args.chip_file}")
        return 1
    
    if args.verbose:
        print(f"Chip: {Path(args.chip_file).name}")
        print(f"=" * 60)
        print(f"Source Image:  {info['source_image']}")
        print(f"Upper Left:    ({info['upper_left_x']}, {info['upper_left_y']})")
        print(f"Lower Right:   ({info['lower_right_x']}, {info['lower_right_y']})")
        print(f"Dimensions:    {info['width']} x {info['height']}")
        print(f"=" * 60)
        print(f"To recreate from source COG:")
        print(f"  gs://tumamoc-2023/cogs/{info['source_image']}.tif")
        print(f"  Coordinates: ({info['upper_left_x']}, {info['upper_left_y']}) to ({info['lower_right_x']}, {info['lower_right_y']})")
    else:
        print(f"{info['source_image']} @ ({info['upper_left_x']},{info['upper_left_y']})")
    
    return 0

if __name__ == "__main__":
    exit(main())



