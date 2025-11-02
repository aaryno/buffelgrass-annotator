#!/usr/bin/env python3
"""
Split training chips geographically for parallel annotation.

This ensures no overlap between annotators = no merge conflicts!
"""

import json
from pathlib import Path
import shutil
from typing import List, Dict
import argparse

def split_chips_evenly(chips_dir: Path, output_dir: Path, num_splits: int = 2):
    """
    Split chips evenly into N groups.
    
    Simple alphabetical split - ensures no overlap.
    """
    chips = sorted(chips_dir.glob("*.png"))
    
    if not chips:
        print(f"❌ No PNG files found in {chips_dir}")
        return
    
    print(f"📊 Found {len(chips)} chips to split into {num_splits} groups")
    
    # Calculate split sizes
    chips_per_group = len(chips) // num_splits
    
    for i in range(num_splits):
        start_idx = i * chips_per_group
        end_idx = start_idx + chips_per_group if i < num_splits - 1 else len(chips)
        
        group_chips = chips[start_idx:end_idx]
        group_dir = output_dir / f"person_{i+1}"
        group_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Creating group {i+1}:")
        print(f"   Output: {group_dir}")
        print(f"   Images: {len(group_chips)} chips")
        print(f"   Range: {group_chips[0].name} to {group_chips[-1].name}")
        
        # Copy chips
        for chip in group_chips:
            shutil.copy2(chip, group_dir / chip.name)
        
        # Create README
        readme = group_dir / "README.txt"
        readme.write_text(f"""
Buffelgrass Annotation - Group {i+1}

Images: {len(group_chips)}
First: {group_chips[0].name}
Last: {group_chips[-1].name}

Instructions:
1. Set up CVAT following: docs/cvat-windows-setup.md
2. Import all images from this folder
3. Annotate using "buffelgrass" label (polygon)
4. Export as COCO format when done
5. Send exported file to project coordinator

Happy annotating! 🌿
""")
    
    print(f"\n✅ Split complete!")
    print(f"   Total groups: {num_splits}")
    print(f"   Output directory: {output_dir}")

def create_manifest(output_dir: Path, num_splits: int):
    """Create a manifest of the split for tracking."""
    manifest = {
        "total_splits": num_splits,
        "groups": []
    }
    
    for i in range(num_splits):
        group_dir = output_dir / f"person_{i+1}"
        chips = list(group_dir.glob("*.png"))
        
        manifest["groups"].append({
            "group_id": i + 1,
            "directory": str(group_dir),
            "num_images": len(chips),
            "first_image": chips[0].name if chips else None,
            "last_image": chips[-1].name if chips else None
        })
    
    manifest_file = output_dir / "split_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📄 Manifest saved: {manifest_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Split training chips for parallel annotation"
    )
    parser.add_argument(
        "chips_dir",
        type=Path,
        help="Directory containing PNG chips to split"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/chips_split"),
        help="Output directory for split groups (default: data/chips_split)"
    )
    parser.add_argument(
        "-n", "--num-splits",
        type=int,
        default=2,
        help="Number of groups to split into (default: 2)"
    )
    
    args = parser.parse_args()
    
    if not args.chips_dir.exists():
        print(f"❌ Error: Directory not found: {args.chips_dir}")
        return 1
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Split chips
    split_chips_evenly(args.chips_dir, args.output, args.num_splits)
    
    # Create manifest
    create_manifest(args.output, args.num_splits)
    
    print("\n🎯 Next steps:")
    print(f"   1. Share each person_N folder with corresponding annotator")
    print(f"   2. Each annotator follows: docs/cvat-windows-setup.md")
    print(f"   3. When done, collect COCO exports from each person")
    print(f"   4. Merge using: python scripts/merge_coco_annotations.py")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())



