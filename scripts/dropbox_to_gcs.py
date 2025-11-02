#!/usr/bin/env python3
"""
Download files from Dropbox shared folder directly to GCS.
Runs in Cloud Shell or Cloud Run - no local download needed!

Setup:
1. Get Dropbox API token: https://www.dropbox.com/developers/apps
2. Set DROPBOX_TOKEN environment variable
3. Run in Cloud Shell or deploy to Cloud Run

Usage:
    export DROPBOX_TOKEN="your_token_here"
    python dropbox_to_gcs.py
"""

import os
import sys
import requests
from google.cloud import storage
from datetime import datetime
import json

# Configuration
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
GCS_BUCKET = "tumamoc-2023"
GCS_PREFIX = "source-jpg/"

# Dropbox shared folder URLs
SHARED_FOLDERS = [
    "https://www.dropbox.com/scl/fo/cxb7mkl80f8ux9sfpfoty/AGhAKqDZ0MNjE4V0ZgrlI6M?rlkey=fu5b5hbr6jo6nn7zsknky4w60",
    "https://www.dropbox.com/scl/fo/pem5nivwv9lgk6rgnc6c4/AAeaBOUbO4qgbshJguxBHZg?rlkey=zkfxodsst7x4ucsoq255pp0mw",
    "https://www.dropbox.com/scl/fo/fuvghz49888ghi2wgpfbg/AAZErLk0UZ27p0ini0Skei0?rlkey=v1kelsdn5a3yv1b723a8ytpwz",
]


def list_shared_folder_files(shared_link):
    """
    List files in a Dropbox shared folder.
    Requires Dropbox API token.
    """
    if not DROPBOX_TOKEN:
        print("❌ DROPBOX_TOKEN not set")
        return []
    
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "path": "",  # Empty path for root of shared folder
        "shared_link": {
            "url": shared_link
        }
    }
    
    response = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        print(f"❌ Dropbox API error: {response.text}")
        return []
    
    result = response.json()
    files = []
    
    for entry in result.get("entries", []):
        if entry.get(".tag") == "file":
            # For shared folders, path is relative to the shared folder root
            file_name = entry.get("name", "unknown")
            file_path = entry.get("path_display") or entry.get("path_lower") or f"/{file_name}"
            
            # Ensure path starts with /
            if not file_path.startswith("/"):
                file_path = f"/{file_path}"
            
            files.append({
                "name": file_name,
                "path": file_path,
                "size": entry.get("size", 0),
                "id": entry.get("id", "")
            })
    
    return files


def download_from_shared_folder(path, shared_link):
    """
    Download file from shared folder using Dropbox API.
    Returns response object for streaming.
    """
    if not DROPBOX_TOKEN:
        return None, "No token"
    
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Dropbox-API-Arg": json.dumps({
            "url": shared_link,
            "path": path
        })
    }
    
    response = requests.post(
        "https://content.dropboxapi.com/2/sharing/get_shared_link_file",
        headers=headers,
        stream=True
    )
    
    if response.status_code == 200:
        return response, None
    
    # Return error message
    error_msg = f"HTTP {response.status_code}"
    try:
        error_data = response.json()
        error_msg = f"{error_msg}: {error_data}"
    except:
        error_msg = f"{error_msg}: {response.text[:200]}"
    
    return None, error_msg


def file_exists_in_gcs(bucket_name, blob_name):
    """Check if a file already exists in GCS."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False


def stream_to_gcs(response, bucket_name, blob_name, chunk_size=8192*1024):
    """
    Stream file from Dropbox response directly to GCS.
    Chunks = 8MB for efficient transfer.
    """
    # Initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Get total size if available (handle both string and int)
    content_length = response.headers.get('content-length', '0')
    total_size = int(content_length) if content_length else 0
    
    # Use upload_from_file with the response stream
    # This is more reliable than blob.open()
    response.raw.decode_content = True
    blob.upload_from_file(response.raw, content_type='image/jpeg', size=total_size)
    
    return f"gs://{bucket_name}/{blob_name}"


def format_size(bytes_size):
    """Format bytes to human-readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def main():
    """Main transfer workflow."""
    
    if not DROPBOX_TOKEN:
        print("=" * 70)
        print("DROPBOX API TOKEN REQUIRED")
        print("=" * 70)
        print()
        print("To use this script with Dropbox API:")
        print("1. Go to: https://www.dropbox.com/developers/apps")
        print("2. Create an app or use existing")
        print("3. Generate access token")
        print("4. Set environment variable:")
        print("   export DROPBOX_TOKEN='your_token_here'")
        print()
        print("=" * 70)
        print()
        print("ALTERNATIVE: Manual file list")
        print("You can also manually list files and use wget/gsutil")
        print("See: scripts/dropbox_to_gcs_manual.sh")
        sys.exit(1)
    
    print("=" * 70)
    print("DROPBOX → GCS DIRECT TRANSFER")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Destination: gs://{GCS_BUCKET}/{GCS_PREFIX}")
    print()
    
    all_files = []
    
    # Step 1: List all files
    print("Step 1: Scanning Dropbox folders...")
    for shared_link in SHARED_FOLDERS:
        print(f"\n  Scanning: {shared_link[:50]}...")
        files = list_shared_folder_files(shared_link)
        print(f"  Found: {len(files)} files")
        
        for f in files:
            f['shared_link'] = shared_link
            all_files.append(f)
    
    if not all_files:
        print("\n❌ No files found or API error")
        sys.exit(1)
    
    # Summary
    total_size = sum(f['size'] for f in all_files)
    print()
    print("=" * 70)
    print(f"Total files: {len(all_files)}")
    print(f"Total size: {format_size(total_size)}")
    print("=" * 70)
    
    # Step 2: Transfer files
    print("\nStep 2: Transferring files to GCS...")
    
    success_count = 0
    failed = []
    
    for i, file_info in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}] {file_info['name']}")
        print(f"  Size: {format_size(file_info['size'])}")
        
        # Check if file already exists in GCS
        gcs_path = f"{GCS_PREFIX}{file_info['name']}"
        if file_exists_in_gcs(GCS_BUCKET, gcs_path):
            print(f"  ⊘ Already exists, skipping")
            success_count += 1
            continue
        
        try:
            # Download from Dropbox
            print("  Downloading from Dropbox...")
            response, error = download_from_shared_folder(
                file_info['path'],
                file_info['shared_link']
            )
            
            if not response:
                raise Exception(f"Download failed: {error}")
            
            # Stream to GCS
            print("  Streaming to GCS...")
            result = stream_to_gcs(response, GCS_BUCKET, gcs_path)
            
            print(f"  ✓ Complete: {result}")
            success_count += 1
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"  ✗ Failed: {e}")
            print(f"  Error details: {error_details[:300]}")
            failed.append({
                'file': file_info['name'],
                'error': str(e)
            })
    
    # Final summary
    print()
    print("=" * 70)
    print("TRANSFER COMPLETE")
    print("=" * 70)
    print(f"Successful: {success_count}/{len(all_files)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed files:")
        for f in failed:
            print(f"  - {f['file']}: {f['error']}")
    
    print()
    print(f"Files available at: gs://{GCS_BUCKET}/{GCS_PREFIX}")
    print(f"Completed: {datetime.now().isoformat()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

