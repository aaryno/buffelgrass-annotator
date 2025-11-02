#!/usr/bin/env python3
"""
Merge COCO annotation files from multiple annotators.

Combines annotations from parallel annotation sessions into a single file.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

def load_coco_file(file_path: Path) -> Dict:
    """Load and validate COCO annotation file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Validate required keys
    required_keys = ['images', 'annotations', 'categories']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Invalid COCO file {file_path}: missing '{key}'")
    
    return data

def merge_coco_annotations(annotation_files: List[Path], output_file: Path):
    """
    Merge multiple COCO annotation files.
    
    Assumes:
    - No overlapping images (different annotators worked on different images)
    - Same category definitions
    """
    
    if not annotation_files:
        print("❌ No annotation files provided")
        return False
    
    print(f"\n📦 Merging {len(annotation_files)} annotation files...\n")
    
    # Load all files
    all_data = []
    for i, file_path in enumerate(annotation_files, 1):
        print(f"📄 Loading file {i}: {file_path.name}")
        try:
            data = load_coco_file(file_path)
            all_data.append(data)
            print(f"   ✓ Images: {len(data['images'])}")
            print(f"   ✓ Annotations: {len(data['annotations'])}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False
    
    # Use first file's metadata and categories
    merged = {
        "info": all_data[0].get("info", {
            "description": "Merged Buffelgrass Annotations",
            "date_created": datetime.now().isoformat()
        }),
        "licenses": all_data[0].get("licenses", []),
        "categories": all_data[0]["categories"],
        "images": [],
        "annotations": []
    }
    
    # Track ID remapping
    image_id_offset = 0
    annotation_id_offset = 0
    
    # Merge each file
    for i, data in enumerate(all_data, 1):
        print(f"\n🔄 Processing file {i}...")
        
        # Verify categories match
        if data["categories"] != merged["categories"]:
            print(f"   ⚠️  Warning: Categories differ in file {i}")
            print(f"   Using categories from first file")
        
        # Remap image IDs
        image_id_map = {}
        for img in data["images"]:
            old_id = img["id"]
            new_id = old_id + image_id_offset
            image_id_map[old_id] = new_id
            
            img_copy = img.copy()
            img_copy["id"] = new_id
            merged["images"].append(img_copy)
        
        # Remap annotation IDs and image references
        for ann in data["annotations"]:
            old_ann_id = ann["id"]
            old_img_id = ann["image_id"]
            
            ann_copy = ann.copy()
            ann_copy["id"] = old_ann_id + annotation_id_offset
            ann_copy["image_id"] = image_id_map[old_img_id]
            merged["annotations"].append(ann_copy)
        
        # Update offsets for next file
        if data["images"]:
            image_id_offset = max(img["id"] for img in merged["images"]) + 1
        if data["annotations"]:
            annotation_id_offset = max(ann["id"] for ann in merged["annotations"]) + 1
        
        print(f"   ✓ Added {len(data['images'])} images")
        print(f"   ✓ Added {len(data['annotations'])} annotations")
    
    # Save merged file
    print(f"\n💾 Saving merged annotations to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Merge Complete!")
    print(f"{'='*60}")
    print(f"Total images:      {len(merged['images'])}")
    print(f"Total annotations: {len(merged['annotations'])}")
    print(f"Categories:        {len(merged['categories'])}")
    print(f"Output file:       {output_file}")
    print(f"{'='*60}\n")
    
    return True

def verify_no_duplicates(merged_file: Path):
    """Verify no duplicate image filenames in merged file."""
    with open(merged_file, 'r') as f:
        data = json.load(f)
    
    filenames = [img["file_name"] for img in data["images"]]
    duplicates = [f for f in filenames if filenames.count(f) > 1]
    
    if duplicates:
        print(f"⚠️  Warning: Found duplicate images:")
        for dup in set(duplicates):
            print(f"   - {dup}")
        return False
    
    print("✓ No duplicate images found")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Merge COCO annotation files from multiple annotators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge two annotation files
  python merge_coco_annotations.py person1.json person2.json -o merged.json
  
  # Merge all JSON files in a directory
  python merge_coco_annotations.py exports/*.json -o merged.json
        """
    )
    parser.add_argument(
        "annotation_files",
        type=Path,
        nargs="+",
        help="COCO annotation JSON files to merge"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/merged_annotations.json"),
        help="Output file for merged annotations (default: data/merged_annotations.json)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify no duplicate images after merging"
    )
    
    args = parser.parse_args()
    
    # Check all files exist
    missing = [f for f in args.annotation_files if not f.exists()]
    if missing:
        print(f"❌ Error: Files not found:")
        for f in missing:
            print(f"   - {f}")
        return 1
    
    # Merge annotations
    success = merge_coco_annotations(args.annotation_files, args.output)
    
    if not success:
        return 1
    
    # Verify if requested
    if args.verify:
        print("\n🔍 Verifying merged file...")
        verify_no_duplicates(args.output)
    
    print("\n🎯 Next steps:")
    print(f"   1. Review merged annotations: {args.output}")
    print(f"   2. Import to GETI using SDK")
    print(f"   3. Begin model training!")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())



