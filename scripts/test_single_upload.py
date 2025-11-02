#!/usr/bin/env python3
"""Test uploading a single file from Dropbox to GCS."""

import os
import sys
import requests
from google.cloud import storage
import json

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
GCS_BUCKET = "tumamoc-2023"

# Test with first file
shared_link = "https://www.dropbox.com/scl/fo/cxb7mkl80f8ux9sfpfoty/AGhAKqDZ0MNjE4V0ZgrlI6M?rlkey=fu5b5hbr6jo6nn7zsknky4w60"
file_path = "/cap-30756.jpg"

print("Testing single file upload...")
print(f"Shared link: {shared_link[:50]}...")
print(f"File: {file_path}")
print()

# Download from Dropbox
print("Downloading from Dropbox...")
headers = {
    "Authorization": f"Bearer {DROPBOX_TOKEN}",
    "Dropbox-API-Arg": json.dumps({
        "url": shared_link,
        "path": file_path
    })
}

response = requests.post(
    "https://content.dropboxapi.com/2/sharing/get_shared_link_file",
    headers=headers,
    stream=True
)

if response.status_code != 200:
    print(f"❌ Download failed: {response.status_code}")
    print(response.text)
    sys.exit(1)

print("✓ Download successful")
content_length = response.headers.get('content-length', '0')
print(f"File size: {int(content_length):,} bytes")
print()

# Upload to GCS
print("Uploading to GCS...")
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob("source-jpg/test-cap-30756.jpg")
    
    # Try simple upload_from_file
    response.raw.decode_content = True
    blob.upload_from_file(response.raw, content_type='image/jpeg')
    
    print(f"✓ Upload successful!")
    print(f"gs://{GCS_BUCKET}/source-jpg/test-cap-30756.jpg")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

