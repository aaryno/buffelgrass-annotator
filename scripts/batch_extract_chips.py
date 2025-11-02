#!/usr/bin/env python3
"""
Batch extract one training chip from each source COG.

Processes all COGs in GCS bucket and generates one random 1024x1024 chip per image.
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from google.cloud import storage
from chip_extractor import generate_chips_for_image

def list_cogs_from_gcs(bucket_name: str, prefix: str = "cogs/"):
    """List all COG files from GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    cog_files = [blob.name for blob in blobs if blob.name.endswith('.tif')]
    return cog_files

def get_chip_subdirectory(image_name: str, output_dir: Path) -> Path:
    """
    Determine which subdirectory (00-99) a chip should go in.
    Uses hash of image name for even distribution.
    """
    hash_val = hash(image_name) % 100
    subdir = output_dir / f"{hash_val:02d}"
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir

def process_cog_batch(
    bucket_name: str,
    cog_prefix: str,
    output_dir: Path,
    chips_per_image: int = 1,
    start_index: int = 0,
    end_index: int = None
):
    """
    Process a batch of COGs and extract chips.
    
    Args:
        bucket_name: GCS bucket name
        cog_prefix: Prefix for COG files in bucket
        output_dir: Local directory to save chips
        chips_per_image: Number of chips per COG (default: 1)
        start_index: Start processing from this index
        end_index: Stop processing at this index (None = process all)
    """
    # List all COGs
    print(f"📋 Listing COGs from gs://{bucket_name}/{cog_prefix}...")
    cog_files = list_cogs_from_gcs(bucket_name, cog_prefix)
    
    if end_index:
        cog_files = cog_files[start_index:end_index]
    else:
        cog_files = cog_files[start_index:]
    
    print(f"✓ Found {len(cog_files)} COGs to process")
    print(f"  Processing range: {start_index} to {start_index + len(cog_files)}")
    print(f"  Output: {output_dir} (distributed across 00-99 subdirectories)")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each COG
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, cog_path in enumerate(cog_files, 1):
        cog_name = Path(cog_path).stem
        
        # Determine subdirectory for this chip
        chip_subdir = get_chip_subdirectory(cog_name, output_dir)
        
        # Check if chip already exists (resume capability)
        # Look for any chip with this image name (provenance naming)
        existing_chips = list(chip_subdir.glob(f"{cog_name}_*.png"))
        if existing_chips:
            print(f"[{i}/{len(cog_files)}] ⊘ {cog_name} (already exists in {chip_subdir.name}/)")
            skip_count += 1
            continue
        
        print(f"[{i}/{len(cog_files)}] 🔄 Processing {cog_name} → {chip_subdir.name}/")
        
        # Download COG temporarily
        temp_file = None
        try:
            # Download COG to temp file
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(cog_path)
            
            with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
                temp_file = tmp.name
                print(f"  ↓ Downloading to temp...")
                blob.download_to_filename(temp_file)
            
            # Generate chip(s) in subdirectory
            print(f"  ✂ Extracting chip(s)...")
            chips = generate_chips_for_image(
                temp_file,
                n_chips=chips_per_image,
                output_dir=str(chip_subdir),
                chip_size=1024,
                output_format='png',
                image_name_override=cog_name  # Use original COG name, not temp file name
            )
            
            print(f"  ✓ Generated {len(chips)} chip(s) in {chip_subdir.name}/")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            fail_count += 1
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
        
        print()
    
    # Summary
    print("=" * 70)
    print("✅ Batch processing complete!")
    print("=" * 70)
    print(f"Total COGs:     {len(cog_files)}")
    print(f"Success:        {success_count}")
    print(f"Skipped:        {skip_count} (already existed)")
    print(f"Failed:         {fail_count}")
    print(f"Output dir:     {output_dir}")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description="Batch extract training chips from all COGs in GCS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 1 chip from each of first 100 COGs
  python batch_extract_chips.py --bucket tumamoc-2023 --end 100
  
  # Extract 1 chip from all COGs
  python batch_extract_chips.py --bucket tumamoc-2023
  
  # Extract 5 chips from each COG (COGs 100-200)
  python batch_extract_chips.py --bucket tumamoc-2023 --start 100 --end 200 -n 5
        """
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="tumamoc-2023",
        help="GCS bucket name (default: tumamoc-2023)"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="cogs/",
        help="Prefix for COG files in bucket (default: cogs/)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/training_chips"),
        help="Output directory for chips (default: data/training_chips)"
    )
    parser.add_argument(
        "-n", "--chips-per-image",
        type=int,
        default=1,
        help="Number of chips per COG (default: 1)"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index (default: 0)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End index (default: None = process all)"
    )
    
    args = parser.parse_args()
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║           Batch Chip Extraction from COGs                     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    # Set GDAL environment for GCS access
    os.environ['CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE'] = 'YES'
    
    # Process COGs
    process_cog_batch(
        args.bucket,
        args.prefix,
        args.output,
        args.chips_per_image,
        args.start,
        args.end
    )
    
    print()
    print("🎯 Next steps:")
    print(f"   1. Review chips in: {args.output}")
    print(f"   2. Split for annotation: make split-dataset")
    print(f"   3. Start annotating with CVAT!")

if __name__ == "__main__":
    main()

