#!/usr/bin/env python3
"""
Create random bin assignments (A-Z) for source COGs.

Assigns each source image to one of 26 bins (A-Z) to break up
sequential flight line patterns. Saves mapping to image-bin.csv.
"""

import sys
import random
import csv
from pathlib import Path
from google.cloud import storage


def list_all_cogs(bucket_name, prefix):
    """List all COG files in GCS bucket."""
    storage_client = storage.Client(project='asdm')
    bucket = storage_client.bucket(bucket_name)
    
    blobs = list(bucket.list_blobs(prefix=prefix))
    cog_files = [
        Path(blob.name).stem  # Just the filename without extension
        for blob in blobs
        if blob.name.endswith('.tif') and not blob.name.endswith('/')
    ]
    
    return sorted(cog_files)


def assign_bins(image_names, num_bins=26, seed=42):
    """
    Randomly assign images to bins (A-Z).
    
    Uses seeded random for reproducibility.
    
    Args:
        image_names: List of image stem names
        num_bins: Number of bins (default 26 for A-Z)
        seed: Random seed for reproducibility
        
    Returns:
        List of (image_name, bin_letter) tuples
    """
    random.seed(seed)
    
    # Create bin labels (A-Z)
    bin_labels = [chr(65 + i) for i in range(num_bins)]  # 65 = 'A'
    
    # Shuffle image list to randomize
    shuffled_images = image_names.copy()
    random.shuffle(shuffled_images)
    
    # Assign to bins in round-robin fashion for even distribution
    assignments = []
    for i, image_name in enumerate(shuffled_images):
        bin_letter = bin_labels[i % num_bins]
        assignments.append((image_name, bin_letter))
    
    # Sort by original image name for easier lookup
    assignments.sort(key=lambda x: x[0])
    
    return assignments


def save_csv(assignments, output_path):
    """Save bin assignments to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['image_name', 'bin'])
        writer.writerows(assignments)


def print_statistics(assignments):
    """Print distribution statistics."""
    from collections import Counter
    
    bins = [bin_letter for _, bin_letter in assignments]
    bin_counts = Counter(bins)
    
    print("\nBin Distribution:")
    print("=" * 50)
    for bin_letter in sorted(bin_counts.keys()):
        count = bin_counts[bin_letter]
        bar = '█' * (count // 2)  # Visual bar chart
        print(f"{bin_letter}: {count:3d} images {bar}")
    
    print("\nStatistics:")
    print(f"  Total images: {len(assignments)}")
    print(f"  Bins: {len(bin_counts)}")
    print(f"  Min per bin: {min(bin_counts.values())}")
    print(f"  Max per bin: {max(bin_counts.values())}")
    print(f"  Avg per bin: {len(assignments) / len(bin_counts):.1f}")


def upload_to_gcs(local_path, bucket_name, gcs_path):
    """Upload CSV to GCS bucket root."""
    storage_client = storage.Client(project='asdm')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type='text/csv')
    print(f"\n✓ Uploaded to gs://{bucket_name}/{gcs_path}")


def main():
    """Create random bin assignments for source images."""
    
    bucket_name = 'tumamoc-2023'
    cog_prefix = 'cogs/'
    output_csv = 'image-bin.csv'
    gcs_path = 'image-bin.csv'  # Root of bucket
    
    print("=" * 70)
    print("Creating Random Bin Assignments (A-Z)")
    print("=" * 70)
    print(f"Source: gs://{bucket_name}/{cog_prefix}")
    print(f"Output: {output_csv} → gs://{bucket_name}/{gcs_path}")
    print()
    
    # List all COGs
    print("Listing source COGs...")
    cog_names = list_all_cogs(bucket_name, cog_prefix)
    print(f"Found {len(cog_names)} COG files")
    print()
    
    if not cog_names:
        print("❌ No COG files found!")
        sys.exit(1)
    
    # Show sample names
    print("Sample COG names:")
    for name in cog_names[:5]:
        print(f"  - {name}")
    if len(cog_names) > 5:
        print(f"  ... and {len(cog_names) - 5} more")
    print()
    
    # Assign to bins
    print("Assigning to bins A-Z...")
    assignments = assign_bins(cog_names, num_bins=26, seed=42)
    
    # Print statistics
    print_statistics(assignments)
    
    # Save locally
    print()
    print(f"Saving to {output_csv}...")
    save_csv(assignments, output_csv)
    print(f"✓ Saved {len(assignments)} assignments")
    
    # Show sample assignments
    print("\nSample assignments:")
    for image_name, bin_letter in assignments[:10]:
        print(f"  {bin_letter}: {image_name}")
    
    # Upload to GCS
    print()
    print(f"Uploading to GCS bucket root...")
    upload_to_gcs(output_csv, bucket_name, gcs_path)
    
    print()
    print("=" * 70)
    print("✓ Complete!")
    print("=" * 70)
    print()
    print("Usage in chip extraction:")
    print("  1. Read image-bin.csv to get bin letter for each COG")
    print("  2. Extract chips: A_{name}.png, B_{name}.png, C_{name}.png, D_{name}.png")
    print("  3. Organize by bin letter into folders")
    print()


if __name__ == "__main__":
    main()

