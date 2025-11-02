#!/usr/bin/env python3
"""
Create shared buffelgrass annotation project in CVAT
Arizona Sonoran Desert Museum - Collaborative Annotation
"""

import argparse
import sys
import time
from pathlib import Path
from getpass import getpass

try:
    from cvat_sdk import make_client
    from cvat_sdk.core.proxies.tasks import ResourceType
except ImportError:
    print("❌ Error: cvat-sdk not installed")
    print("\nInstall with: pip install cvat-sdk")
    sys.exit(1)


# Shared project configuration for all annotators
PROJECT_CONFIG = {
    "name": "Buffelgrass Detection - ASDM",
    "labels": [
        {
            "name": "buffelgrass",
            "color": "#ff0000",  # Red
            "attributes": []
        },
        {
            "name": "soil",
            "color": "#8b4513",  # Brown
            "attributes": []
        },
        {
            "name": "road",
            "color": "#808080",  # Gray
            "attributes": []
        },
        {
            "name": "building",
            "color": "#800080",  # Purple
            "attributes": []
        },
        {
            "name": "car",
            "color": "#ffd700",  # Gold
            "attributes": []
        },
        {
            "name": "tree_shrub",
            "color": "#228b22",  # Forest green
            "attributes": []
        },
        {
            "name": "cactus",
            "color": "#00ff00",  # Bright green
            "attributes": []
        },
        {
            "name": "other_grass",
            "color": "#90ee90",  # Light green
            "attributes": []
        },
    ]
}


def create_project(client, config):
    """Create or get existing project with standard configuration"""
    
    print(f"\n📁 Setting up project: {config['name']}")
    
    # Check if project exists
    for project in client.projects.list():
        if project.name == config['name']:
            print(f"✅ Project already exists (ID: {project.id})")
            return project
    
    # Create new project
    print("Creating new project...")
    project = client.projects.create(config)
    print(f"✅ Project created (ID: {project.id})")
    
    return project


def create_task(client, project_id, username, chips_dir):
    """Create annotation task with user's training chips"""
    
    task_name = f"Buffelgrass Training Set - {username}"
    
    print(f"\n📋 Setting up task: {task_name}")
    
    # Check if task exists
    for task in client.tasks.list():
        if task.name == task_name:
            print(f"✅ Task already exists (ID: {task.id})")
            print(f"   URL: http://localhost:8080/tasks/{task.id}")
            return task
    
    # Find image files
    chips_path = Path(chips_dir)
    if not chips_path.exists():
        print(f"⚠️  Chips directory not found: {chips_dir}")
        print("   Creating task without images - you can add them later via web UI")
        image_files = []
    else:
        # Support multiple image formats
        image_files = []
        for ext in ['*.tif', '*.tiff', '*.jpg', '*.jpeg', '*.png']:
            image_files.extend(chips_path.glob(ext))
        image_files = sorted(image_files)
        
        if not image_files:
            print(f"⚠️  No image files found in: {chips_dir}")
            print("   Supported formats: .tif, .tiff, .jpg, .jpeg, .png")
            print("   Creating task without images - you can add them later via web UI")
    
    # Create task
    task_spec = {
        "name": task_name,
        "project_id": project_id,
        "segment_size": 0,  # All images in one job
    }
    
    print("Creating task...")
    if image_files:
        print(f"Found {len(image_files)} images to upload...")
        task_spec["resources"] = [ResourceType.LOCAL]
        task_spec["files"] = [str(f) for f in image_files]
    
    task = client.tasks.create_from_data(
        spec=task_spec,
        resource_type=ResourceType.LOCAL,
        resources=[str(f) for f in image_files] if image_files else []
    )
    
    print(f"✅ Task created (ID: {task.id})")
    print(f"   Images: {len(image_files)}")
    print(f"   URL: http://localhost:8080/tasks/{task.id}")
    
    return task


def main():
    parser = argparse.ArgumentParser(
        description="Setup shared buffelgrass annotation project in CVAT"
    )
    parser.add_argument(
        '--username',
        required=True,
        help='Your CVAT username'
    )
    parser.add_argument(
        '--password',
        help='Your CVAT password (will prompt if not provided)'
    )
    parser.add_argument(
        '--chips-dir',
        default='./chips',
        help='Directory containing your training chip images (default: ./chips)'
    )
    parser.add_argument(
        '--host',
        default='http://localhost:8080',
        help='CVAT server URL (default: http://localhost:8080)'
    )
    
    args = parser.parse_args()
    
    # Get password if not provided
    password = args.password or getpass(f"Password for {args.username}: ")
    
    print("=" * 60)
    print("  CVAT Buffelgrass Project Setup")
    print("  Arizona Sonoran Desert Museum")
    print("=" * 60)
    
    # Connect to CVAT
    print(f"\n🔌 Connecting to CVAT at {args.host}...")
    try:
        client = make_client(
            host=args.host,
            credentials=(args.username, password)
        )
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Is CVAT running? Check http://localhost:8080")
        print("2. Is username/password correct?")
        print("3. Did you create an account in the web UI?")
        sys.exit(1)
    
    # Create/get project
    try:
        project = create_project(client, PROJECT_CONFIG)
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        sys.exit(1)
    
    # Create task with user's chips
    try:
        task = create_task(client, project.id, args.username, args.chips_dir)
    except Exception as e:
        print(f"❌ Failed to create task: {e}")
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    print(f"\nProject: {PROJECT_CONFIG['name']}")
    print(f"Task: Buffelgrass Training Set - {args.username}")
    print(f"\n🎨 Start annotating:")
    print(f"   http://localhost:8080/tasks/{task.id}")
    print("\n📚 Remember:")
    print("   - Focus on buffelgrass (red label)")
    print("   - Save frequently (Ctrl+S)")
    print("   - Export as COCO 1.0 when complete")
    print("   - Send exported ZIP to project coordinator")
    print("\nHappy annotating! 🌵")
    print()


if __name__ == '__main__':
    main()


