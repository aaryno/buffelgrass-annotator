#!/usr/bin/env python3
"""
Extract random chips from Cloud-Optimized GeoTIFF files for model training.

Generates random 1024x1024 pixel chips from source imagery, ensuring:
- Chips don't intersect image boundaries
- Full resolution extraction
- Random spatial sampling
"""

import rasterio
from rasterio.windows import Window
import numpy as np
from pathlib import Path
import random
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class ChipCoords:
    """Coordinates for a chip in image space."""
    ul_x: int  # Upper-left X (column)
    ul_y: int  # Upper-left Y (row)
    width: int
    height: int
    
    @property
    def lr_x(self):
        """Lower-right X coordinate."""
        return self.ul_x + self.width
    
    @property
    def lr_y(self):
        """Lower-right Y coordinate."""
        return self.ul_y + self.height
    
    def is_valid(self, image_width: int, image_height: int) -> bool:
        """
        Check if chip coordinates are valid (within image bounds).
        
        Args:
            image_width: Width of source image
            image_height: Height of source image
            
        Returns:
            True if chip is fully contained within image bounds
        """
        return (
            self.ul_x > 0 and
            self.ul_y > 0 and
            self.lr_x < image_width and
            self.lr_y < image_height
        )
    
    def to_window(self) -> Window:
        """Convert to rasterio Window."""
        return Window(self.ul_x, self.ul_y, self.width, self.height)


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """
    Get image dimensions without loading full data.
    
    Args:
        image_path: Path to image file (local or GCS URL)
        
    Returns:
        (width, height) tuple
    """
    with rasterio.open(image_path) as src:
        return src.width, src.height


def generate_random_chip_coords(
    image_width: int,
    image_height: int,
    chip_width: int = 1024,
    chip_height: int = 1024,
    margin: int = 1
) -> ChipCoords:
    """
    Generate random chip coordinates within image bounds.
    
    Args:
        image_width: Width of source image
        image_height: Height of source image
        chip_width: Desired chip width
        chip_height: Desired chip height
        margin: Minimum distance from image edges (default 1 pixel)
        
    Returns:
        ChipCoords object with valid coordinates
        
    Raises:
        ValueError: If chip dimensions exceed image dimensions
    """
    # Validate chip fits in image
    if chip_width >= image_width - (2 * margin):
        raise ValueError(
            f"Chip width ({chip_width}) too large for image width "
            f"({image_width}) with margin ({margin})"
        )
    if chip_height >= image_height - (2 * margin):
        raise ValueError(
            f"Chip height ({chip_height}) too large for image height "
            f"({image_height}) with margin ({margin})"
        )
    
    # Calculate valid ranges for upper-left corner
    # UL must be > margin, and LR must be < (dimension - margin)
    max_ul_x = image_width - chip_width - margin
    max_ul_y = image_height - chip_height - margin
    
    # Generate random coordinates
    ul_x = random.randint(margin, max_ul_x)
    ul_y = random.randint(margin, max_ul_y)
    
    coords = ChipCoords(ul_x, ul_y, chip_width, chip_height)
    
    # Verify validity
    assert coords.is_valid(image_width, image_height), \
        f"Generated invalid coordinates: {coords}"
    
    return coords


def extract_chip(
    image_path: str,
    chip_coords: ChipCoords,
    output_path: str = None,
    output_format: str = 'png'
) -> np.ndarray:
    """
    Extract a chip from source image at full resolution.
    
    Args:
        image_path: Path to source image (local or GCS URL)
        chip_coords: Chip coordinates
        output_path: Optional path to save chip
        output_format: Output format ('png', 'tif', or 'jpeg')
        
    Returns:
        Numpy array of chip data (bands, height, width)
    """
    with rasterio.open(image_path) as src:
        # Read chip data using window
        window = chip_coords.to_window()
        chip_data = src.read(window=window)
        
        # Save if output path provided
        if output_path:
            if output_format.lower() in ['png', 'jpeg', 'jpg']:
                # For PNG/JPEG: save as standard image format for GETI
                # Remove geospatial metadata, keep only RGB data
                from PIL import Image
                
                # Convert from (bands, height, width) to (height, width, bands)
                img_data = np.transpose(chip_data, (1, 2, 0))
                
                # Create PIL Image
                img = Image.fromarray(img_data, mode='RGB')
                
                # Save as PNG or JPEG
                img.save(output_path, format=output_format.upper())
            else:
                # For GeoTIFF: preserve geospatial metadata
                profile = src.profile.copy()
                profile.update({
                    'width': chip_coords.width,
                    'height': chip_coords.height,
                    'transform': rasterio.windows.transform(window, src.transform)
                })
                
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(chip_data)
        
        return chip_data


def generate_chips_for_image(
    image_path: str,
    n_chips: int,
    output_dir: str = None,
    chip_size: int = 1024,
    output_format: str = 'png',
    image_name_override: str = None
) -> List[Tuple[ChipCoords, np.ndarray]]:
    """
    Generate multiple random chips from a single image.
    
    Args:
        image_path: Path to source image
        n_chips: Number of chips to generate
        output_dir: Optional directory to save chips
        chip_size: Size of square chips (default 1024x1024)
        output_format: Output format ('png', 'tif', or 'jpeg')
        image_name_override: Override image name in output (useful for temp files)
        
    Returns:
        List of (coordinates, chip_data) tuples
    """
    # Get image dimensions
    width, height = get_image_dimensions(image_path)
    print(f"Image dimensions: {width} x {height}")
    print(f"Output format: {output_format.upper()}")
    
    # Generate chips
    chips = []
    image_name = image_name_override if image_name_override else Path(image_path).stem
    
    # Determine file extension
    ext_map = {'png': '.png', 'jpeg': '.jpg', 'jpg': '.jpg', 'tif': '.tif'}
    ext = ext_map.get(output_format.lower(), '.png')
    
    for i in range(n_chips):
        # Generate random coordinates
        coords = generate_random_chip_coords(width, height, chip_size, chip_size)
        
        # Prepare output path if directory provided
        output_path = None
        if output_dir:
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            # Use provenance naming: {image_name}_{ulx}_{uly}_{width}_{height}.png
            output_path = output_dir_path / f"{image_name}_{coords.ul_x}_{coords.ul_y}_{coords.width}_{coords.height}{ext}"
        
        # Extract chip
        print(f"  Chip {i+1}/{n_chips}: UL=({coords.ul_x}, {coords.ul_y}) "
              f"LR=({coords.lr_x}, {coords.lr_y})")
        chip_data = extract_chip(image_path, coords, output_path, output_format)
        
        if output_path:
            print(f"    Saved to: {output_path}")
        
        chips.append((coords, chip_data))
    
    return chips


def main():
    """Test chip extraction with example image."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract random chips from COG imagery'
    )
    parser.add_argument(
        'image_path',
        help='Path to source image (local or gs:// URL)'
    )
    parser.add_argument(
        '-n', '--n-chips',
        type=int,
        default=5,
        help='Number of chips to generate (default: 5)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for chips'
    )
    parser.add_argument(
        '-s', '--chip-size',
        type=int,
        default=1024,
        help='Chip size in pixels (default: 1024)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['png', 'jpeg', 'tif'],
        default='png',
        help='Output format (default: png, recommended for GETI)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CHIP EXTRACTOR")
    print("=" * 70)
    print(f"Source: {args.image_path}")
    print(f"Chips: {args.n_chips}")
    print(f"Size: {args.chip_size}x{args.chip_size}")
    if args.output_dir:
        print(f"Output: {args.output_dir}")
    print()
    
    # Generate chips
    chips = generate_chips_for_image(
        args.image_path,
        args.n_chips,
        args.output_dir,
        args.chip_size,
        args.format
    )
    
    print()
    print(f"✓ Generated {len(chips)} chips")
    print(f"  Chip shape: {chips[0][1].shape}")


if __name__ == "__main__":
    main()

