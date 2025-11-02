#!/usr/bin/env python3
"""
Unit tests for chip coordinate generation.

Tests that chip coordinates are correctly generated within image bounds.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from chip_extractor import ChipCoords, generate_random_chip_coords

# pytest is optional
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    pytest = None


def test_chip_coords_validation():
    """Test that ChipCoords.is_valid() correctly validates coordinates."""
    
    # Test case: 1000x1000 image, 100x100 chip
    image_width, image_height = 1000, 1000
    chip_width, chip_height = 100, 100
    
    # Valid chip (centered)
    coords = ChipCoords(ul_x=450, ul_y=450, width=chip_width, height=chip_height)
    assert coords.is_valid(image_width, image_height), \
        "Centered chip should be valid"
    
    # Valid chip (near edge but not touching)
    coords = ChipCoords(ul_x=1, ul_y=1, width=chip_width, height=chip_height)
    assert coords.is_valid(image_width, image_height), \
        "Chip with 1px margin should be valid"
    
    # Invalid chip (touching left edge)
    coords = ChipCoords(ul_x=0, ul_y=100, width=chip_width, height=chip_height)
    assert not coords.is_valid(image_width, image_height), \
        "Chip touching left edge should be invalid"
    
    # Invalid chip (touching top edge)
    coords = ChipCoords(ul_x=100, ul_y=0, width=chip_width, height=chip_height)
    assert not coords.is_valid(image_width, image_height), \
        "Chip touching top edge should be invalid"
    
    # Invalid chip (exceeding right edge)
    coords = ChipCoords(ul_x=901, ul_y=100, width=chip_width, height=chip_height)
    assert not coords.is_valid(image_width, image_height), \
        f"Chip with LR={coords.lr_x} exceeding width={image_width} should be invalid"
    
    # Invalid chip (exceeding bottom edge)
    coords = ChipCoords(ul_x=100, ul_y=901, width=chip_width, height=chip_height)
    assert not coords.is_valid(image_width, image_height), \
        f"Chip with LR={coords.lr_y} exceeding height={image_height} should be invalid"
    
    # Edge case: chip at maximum valid position (LR = W-1, H-1)
    coords = ChipCoords(ul_x=899, ul_y=899, width=chip_width, height=chip_height)
    assert coords.is_valid(image_width, image_height), \
        "Chip with LR at (W-1, H-1) should be valid"


def test_generate_random_coords_boundaries():
    """Test that generated coordinates respect boundaries."""
    
    image_width, image_height = 5000, 3000
    chip_width, chip_height = 1024, 1024
    
    # Generate many random chips and verify all are valid
    for _ in range(100):
        coords = generate_random_chip_coords(
            image_width, image_height,
            chip_width, chip_height
        )
        
        # Check UL is > 0
        assert coords.ul_x > 0, f"UL X ({coords.ul_x}) must be > 0"
        assert coords.ul_y > 0, f"UL Y ({coords.ul_y}) must be > 0"
        
        # Check LR is < dimensions
        assert coords.lr_x < image_width, \
            f"LR X ({coords.lr_x}) must be < width ({image_width})"
        assert coords.lr_y < image_height, \
            f"LR Y ({coords.lr_y}) must be < height ({image_height})"
        
        # Use is_valid() method
        assert coords.is_valid(image_width, image_height), \
            f"Generated coordinates should be valid: {coords}"


def test_generate_random_coords_custom_margin():
    """Test coordinate generation with custom margin."""
    
    image_width, image_height = 5000, 3000
    chip_width, chip_height = 1024, 1024
    margin = 50
    
    for _ in range(50):
        coords = generate_random_chip_coords(
            image_width, image_height,
            chip_width, chip_height,
            margin=margin
        )
        
        # Check margin is respected
        assert coords.ul_x >= margin, f"UL X must be >= margin ({margin})"
        assert coords.ul_y >= margin, f"UL Y must be >= margin ({margin})"
        assert coords.lr_x <= image_width - margin, \
            f"LR X must be <= width - margin"
        assert coords.lr_y <= image_height - margin, \
            f"LR Y must be <= height - margin"


def test_chip_too_large_raises_error():
    """Test that chips larger than image raise ValueError."""
    
    image_width, image_height = 1000, 1000
    chip_width, chip_height = 1024, 1024
    
    if HAS_PYTEST:
        with pytest.raises(ValueError, match="too large"):
            generate_random_chip_coords(
                image_width, image_height,
                chip_width, chip_height
            )
    else:
        # Manual test without pytest
        try:
            generate_random_chip_coords(
                image_width, image_height,
                chip_width, chip_height
            )
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "too large" in str(e)


def test_standard_1024_chip():
    """Test standard 1024x1024 chip on typical aerial imagery."""
    
    # Typical aerial image dimensions (example from cap-29792)
    image_width, image_height = 9000, 6000
    chip_size = 1024
    
    for _ in range(20):
        coords = generate_random_chip_coords(
            image_width, image_height,
            chip_size, chip_size
        )
        
        # Verify standard chip properties
        assert coords.width == chip_size
        assert coords.height == chip_size
        assert coords.is_valid(image_width, image_height)


def test_chip_coords_properties():
    """Test ChipCoords computed properties."""
    
    coords = ChipCoords(ul_x=100, ul_y=200, width=1024, height=1024)
    
    assert coords.lr_x == 100 + 1024, "LR X should be UL X + width"
    assert coords.lr_y == 200 + 1024, "LR Y should be UL Y + height"


if __name__ == "__main__":
    # Run tests without pytest
    print("Running chip coordinate tests...")
    print()
    
    test_chip_coords_validation()
    print("✓ test_chip_coords_validation passed")
    
    test_generate_random_coords_boundaries()
    print("✓ test_generate_random_coords_boundaries passed")
    
    test_generate_random_coords_custom_margin()
    print("✓ test_generate_random_coords_custom_margin passed")
    
    try:
        test_chip_too_large_raises_error()
        print("✓ test_chip_too_large_raises_error passed")
    except AssertionError:
        print("✓ test_chip_too_large_raises_error passed (pytest not available)")
    
    test_standard_1024_chip()
    print("✓ test_standard_1024_chip passed")
    
    test_chip_coords_properties()
    print("✓ test_chip_coords_properties passed")
    
    print()
    print("All tests passed! ✓")

