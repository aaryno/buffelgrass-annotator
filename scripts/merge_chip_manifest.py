#!/usr/bin/env python3
"""
Merge partial chip manifests from Cloud Run tasks into single CSV.

Downloads all partial CSVs from GCS, merges them, and uploads final manifest.
"""

import csv
import tempfile
from pathlib import Path
from google.cloud import storage
from collections import Counter


def download_partial_manifests(bucket_name: str, prefix: str = "chip_manifests/partial/"):
    """Download all partial manifest CSVs."""
    storage_client = storage.Client(project='asdm')
    bucket = storage_client.bucket(bucket_name)
    
    blobs = list(bucket.list_blobs(prefix=prefix))
    csv_blobs = [b for b in blobs if b.name.endswith('.csv')]
    
    print(f"Found {len(csv_blobs)} partial manifests")
    
    temp_dir = tempfile.mkdtemp()
    local_files = []
    
    for blob in csv_blobs:
        local_path = Path(temp_dir) / Path(blob.name).name
        blob.download_to_filename(str(local_path))
        local_files.append(str(local_path))
        print(f"  Downloaded: {blob.name}")
    
    return local_files


def merge_manifests(local_files: list, output_path: str):
    """Merge all CSV files into one."""
    all_rows = []
    
    for filepath in local_files:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            all_rows.extend(rows)
            print(f"  Loaded {len(rows)} rows from {Path(filepath).name}")
    
    # Sort by source_image and ulx for consistent ordering
    all_rows.sort(key=lambda r: (r['source_image'], int(r['ulx']), int(r['uly'])))
    
    # Write merged CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['chip_path', 'source_image', 'ulx', 'uly', 'width', 'height'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    return all_rows


def print_statistics(rows: list):
    """Print manifest statistics."""
    from collections import Counter
    
    bins = [Path(r['chip_path']).parent.name for r in rows]
    sources = [r['source_image'] for r in rows]
    
    bin_counts = Counter(bins)
    source_counts = Counter(sources)
    
    print("\n" + "=" * 70)
    print("Manifest Statistics")
    print("=" * 70)
    print(f"Total chip windows: {len(rows):,}")
    print(f"Source images: {len(source_counts):,}")
    print(f"Unique bins: {len(bin_counts)}")
    print(f"Avg chips per source: {len(rows) / len(source_counts):.1f}")
    print(f"Avg chips per bin: {len(rows) / len(bin_counts):.1f}")
    print()
    
    print("Chips per source (sample):")
    for source, count in list(source_counts.most_common(5)):
        print(f"  {source}: {count} chips")
    print()
    
    print("Bins with most chips (top 10):")
    for bin_label, count in bin_counts.most_common(10):
        print(f"  {bin_label}: {count} chips")
    print()
    
    print("Bins with fewest chips (bottom 10):")
    for bin_label, count in list(bin_counts.most_common())[-10:]:
        print(f"  {bin_label}: {count} chips")


def upload_manifest(local_path: str, bucket_name: str, gcs_path: str):
    """Upload final manifest to GCS."""
    storage_client = storage.Client(project='asdm')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type='text/csv')
    print(f"\n✓ Uploaded to gs://{bucket_name}/{gcs_path}")


def main():
    """Merge partial manifests."""
    bucket_name = 'tumamoc-2023'
    output_gcs_path = 'chip-manifest.csv'
    local_output = 'chip-manifest.csv'
    
    print("=" * 70)
    print("Merging Chip Manifests")
    print("=" * 70)
    print()
    
    # Download partial manifests
    print("Downloading partial manifests...")
    partial_files = download_partial_manifests(bucket_name)
    print()
    
    # Merge
    print("Merging...")
    rows = merge_manifests(partial_files, local_output)
    print()
    
    # Statistics
    print_statistics(rows)
    
    # Upload
    print()
    print("Uploading final manifest...")
    upload_manifest(local_output, bucket_name, output_gcs_path)
    
    print()
    print("=" * 70)
    print("✓ Complete!")
    print("=" * 70)
    print(f"\nLocal file: {local_output}")
    print(f"GCS file: gs://{bucket_name}/{output_gcs_path}")
    print()
    print("To sample chips:")
    print(f"  # Sample 1000 chips from bin 'rf'")
    print(f"  grep '^rf/' chip-manifest.csv | head -1000")
    print()


if __name__ == "__main__":
    main()


