#!/usr/bin/env python3
"""
Cloud Run Job for parallel Dropbox → GCS transfer
Each task processes every Nth file based on task index
"""

import os
import sys
import json
import requests
from google.cloud import storage

# Configuration from environment
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
GCS_BUCKET = os.getenv("GCS_BUCKET", "tumamoc-2023")
GCS_PREFIX = os.getenv("GCS_PREFIX", "source-jpg/")

# Dropbox shared folder URLs
SHARED_LINKS = [
    "https://www.dropbox.com/scl/fo/cxb7mkl80f8ux9sfpfoty/AGhAKqDZ0MNjE4V0ZgrlI6M?rlkey=fu5b5hbr6jo6nn7zsknky4w60&e=1&dl=0",
]

def list_shared_folder_files(shared_link):
    """List all files in a Dropbox shared folder"""
    if not DROPBOX_TOKEN:
        return []
    
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "path": "",
        "shared_link": {"url": shared_link}
    }
    
    try:
        response = requests.post(
            "https://api.dropboxapi.com/2/files/list_folder",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            print(f"Error listing folder: {response.status_code}")
            return []
        
        result = response.json()
        files = []
        
        for entry in result.get("entries", []):
            if entry.get(".tag") == "file":
                file_name = entry.get("name", "unknown")
                file_path = entry.get("path_display") or entry.get("path_lower") or f"/{file_name}"
                if not file_path.startswith("/"):
                    file_path = f"/{file_path}"
                files.append({
                    "name": file_name,
                    "path": file_path,
                    "size": entry.get("size", 0),
                    "shared_link": shared_link
                })
        
        return files
    except Exception as e:
        print(f"Exception listing folder: {e}")
        return []

def file_exists_in_gcs(bucket_name, blob_name):
    """Check if file exists in GCS"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False

def download_from_shared_folder(path, shared_link):
    """Download file from Dropbox shared folder"""
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
    
    error_msg = f"HTTP {response.status_code}"
    try:
        error_data = response.json()
        error_msg = f"{error_msg}: {error_data}"
    except:
        error_msg = f"{error_msg}: {response.text[:200]}"
    
    return None, error_msg

def stream_to_gcs(response, bucket_name, blob_name):
    """Stream file directly to GCS"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    content_length = response.headers.get('content-length', '0')
    total_size = int(content_length) if content_length else 0
    
    response.raw.decode_content = True
    blob.upload_from_file(response.raw, content_type='image/jpeg', size=total_size)
    
    return f"gs://{bucket_name}/{blob_name}"

def main():
    # Get task index and count from Cloud Run
    task_index = int(os.getenv("CLOUD_RUN_TASK_INDEX", "0"))
    task_count = int(os.getenv("CLOUD_RUN_TASK_COUNT", "1"))
    
    print(f"╔{'═'*68}╗")
    print(f"║  Dropbox → GCS Transfer Worker {task_index+1}/{task_count}".ljust(68) + " ║")
    print(f"╚{'═'*68}╝\n")
    
    if not DROPBOX_TOKEN:
        print("❌ ERROR: DROPBOX_TOKEN not set")
        sys.exit(1)
    
    # List all files from all shared folders
    print("📋 Listing files from Dropbox shared folders...")
    all_files = []
    for link in SHARED_LINKS:
        files = list_shared_folder_files(link)
        all_files.extend(files)
        print(f"   Found {len(files)} files in folder")
    
    print(f"\n   Total files: {len(all_files)}")
    
    # Filter to only files this worker should process
    my_files = [f for i, f in enumerate(all_files) if i % task_count == task_index]
    print(f"   Worker {task_index+1} assigned: {len(my_files)} files\n")
    
    # Process files
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, file_info in enumerate(my_files, 1):
        gcs_path = f"{GCS_PREFIX}{file_info['name']}"
        size_mb = file_info['size'] / (1024 * 1024)
        
        # Skip if exists
        if file_exists_in_gcs(GCS_BUCKET, gcs_path):
            print(f"  [{i}/{len(my_files)}] ⊘ {file_info['name']} ({size_mb:.1f} MB) - already exists")
            skip_count += 1
            continue
        
        # Download and upload
        print(f"  [{i}/{len(my_files)}] 📥 {file_info['name']} ({size_mb:.1f} MB)...", end='', flush=True)
        
        try:
            response, error = download_from_shared_folder(
                file_info['path'],
                file_info['shared_link']
            )
            
            if error:
                print(f" ✗ Download failed: {error}")
                fail_count += 1
                continue
            
            print(" 📤", end='', flush=True)
            gcs_url = stream_to_gcs(response, GCS_BUCKET, gcs_path)
            print(f" ✓")
            success_count += 1
            
        except Exception as e:
            print(f" ✗ Error: {str(e)[:60]}")
            fail_count += 1
    
    # Summary
    print(f"\n{'═'*70}")
    print(f"✓ Worker {task_index+1} complete!")
    print(f"  Processed: {len(my_files)}")
    print(f"  Success:   {success_count}")
    print(f"  Skipped:   {skip_count} (already existed)")
    print(f"  Failed:    {fail_count}")
    print(f"{'═'*70}\n")

if __name__ == "__main__":
    main()



