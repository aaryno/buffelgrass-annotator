#!/usr/bin/env python3
"""
Batch extract training chips from all COGs in GCS bucket.
Downloads COGs temporarily, extracts chips, uploads to training_chips/.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import List

try:
    from google.cloud import storage
    import subprocess
except ImportError:
    print("❌ Missing dependencies. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-storage"])
    from google.cloud import storage
    import subprocess


def list_cogs(bucket_name: str, prefix: str = "cogs/") -> List[str]:
    """List all COG files in GCS bucket."""
    print(f"📋 Listing COGs in gs://{bucket_name}/{prefix}...")
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    cog_files = []
    for blob in blobs:
        if blob.name.endswith(('.tif', '.tiff')):
            cog_files.append(blob.name)
    
    return cog_files


def extract_chips_from_cog(
    bucket_name: str,
    cog_path: str,
    n_chips: int,
    output_dir: Path,
    temp_dir: Path,
) -> int:
    """Download COG, extract chips, clean up."""
    cog_filename = Path(cog_path).name
    print(f"\n🔬 Processing: {cog_filename}")
    
    # Download COG to temp directory
    local_cog = temp_dir / cog_filename
    print(f"   ⬇️  Downloading...")
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(cog_path)
    blob.download_to_filename(str(local_cog))
    
    # Extract chips using existing chip_extractor.py
    print(f"   ✂️  Extracting {n_chips} chips...")
    
    chip_script = Path(__file__).parent / "chip_extractor.py"
    cmd = [
        sys.executable,
        str(chip_script),
        str(local_cog),
        "-n", str(n_chips),
        "-o", str(output_dir),
        "-f", "png",  # PNG for annotation tools
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Count extracted chips
        num_chips = len([line for line in result.stdout.split('\n') if 'Saved to:' in line])
        print(f"   ✅ Extracted {num_chips} chips")
        
        # Clean up downloaded COG
        local_cog.unlink()
        
        return num_chips
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to extract chips: {e}")
        print(f"   Error output: {e.stderr}")
        if local_cog.exists():
            local_cog.unlink()
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch extract training chips from COGs in GCS"
    )
    parser.add_argument(
        "--bucket",
        default="tumamoc-2023",
        help="GCS bucket name (default: tumamoc-2023)"
    )
    parser.add_argument(
        "--prefix",
        default="cogs/",
        help="GCS prefix/folder (default: cogs/)"
    )
    parser.add_argument(
        "--n-chips",
        type=int,
        default=10,
        help="Number of chips to extract per COG (default: 10)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./data/training_chips"),
        help="Local output directory (default: ./data/training_chips)"
    )
    parser.add_argument(
        "--max-cogs",
        type=int,
        help="Maximum number of COGs to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🌾 Batch Chip Extraction")
    print("=" * 60)
    print(f"Bucket: gs://{args.bucket}/{args.prefix}")
    print(f"Chips per image: {args.n_chips}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)
    print()
    
    # List COGs
    cog_files = list_cogs(args.bucket, args.prefix)
    
    if not cog_files:
        print("❌ No COG files found")
        return 1
    
    print(f"✅ Found {len(cog_files)} COG files")
    
    if args.max_cogs:
        cog_files = cog_files[:args.max_cogs]
        print(f"   Processing first {args.max_cogs} files only")
    
    print()
    
    # Process each COG
    total_chips = 0
    successful = 0
    failed = 0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for i, cog_path in enumerate(cog_files, 1):
            print(f"[{i}/{len(cog_files)}] ", end='')
            
            try:
                num_chips = extract_chips_from_cog(
                    args.bucket,
                    cog_path,
                    args.n_chips,
                    args.output_dir,
                    temp_path,
                )
                
                if num_chips > 0:
                    total_chips += num_chips
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed += 1
    
    # Summary
    print()
    print("=" * 60)
    print("✅ Batch Extraction Complete!")
    print("=" * 60)
    print(f"Processed: {len(cog_files)} COGs")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total chips: {total_chips}")
    print(f"Output directory: {args.output_dir}")
    print()
    print("Next steps:")
    print(f"  1. Review chips in {args.output_dir}/")
    print("  2. Upload to CVAT: make cvat-setup-project")
    print("  3. Start annotating!")
    print()
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

