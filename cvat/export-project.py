#!/usr/bin/env python3
"""
Export CVAT project for sharing with collaborators.
Creates a backup that can be imported on another CVAT instance.
"""

import os
import sys
from pathlib import Path

try:
    from cvat_sdk import make_client
except ImportError:
    print("❌ cvat-sdk not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cvat-sdk"])
    from cvat_sdk import make_client


def export_project(
    host: str = "http://localhost:8080",
    username: str = None,
    password: str = None,
    project_name: str = "Buffelgrass Detection",
    output_dir: str = "./cvat/exports"
):
    """Export CVAT project to file."""
    
    # Get credentials
    if not username:
        if os.path.exists(".cvat.env"):
            # Load from .cvat.env
            with open(".cvat.env") as f:
                for line in f:
                    if line.startswith("CVAT_USERNAME"):
                        username = line.split("=")[1].strip()
                    elif line.startswith("CVAT_PASSWORD"):
                        password = line.split("=")[1].strip()
        else:
            username = input("CVAT Username: ")
            password = input("CVAT Password: ")
    
    print(f"🔗 Connecting to CVAT at {host}...")
    client = make_client(host=host, credentials=(username, password))
    print(f"✅ Connected as {username}")
    
    # Find project
    print(f"\n📁 Finding project: {project_name}")
    projects = client.projects.list()
    project = None
    for proj in projects:
        if proj.name == project_name:
            project = proj
            break
    
    if not project:
        print(f"❌ Project '{project_name}' not found")
        return False
    
    print(f"✅ Found project (ID: {project.id})")
    
    # Export
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    export_file = output_path / f"{project_name.lower().replace(' ', '-')}-export.zip"
    
    # Get all tasks in the project
    tasks = [task for task in client.tasks.list() if task.project_id == project.id]
    print(f"   Found {len(tasks)} task(s) in project")
    
    if not tasks:
        print("❌ No tasks found in project")
        return False
    
    print(f"\n📦 Exporting annotations...")
    print(f"   Output directory: {output_path}")
    
    try:
        # Export each task's annotations in COCO format
        for i, task in enumerate(tasks, 1):
            task_name = task.name.lower().replace(" ", "-")
            task_export_file = output_path / f"{task_name}-coco.zip"
            
            print(f"   [{i}/{len(tasks)}] Exporting task: {task.name}")
            
            # Download COCO annotations for the task
            task_obj = client.tasks.retrieve(task.id)
            task_obj.export_dataset("COCO 1.0", str(task_export_file), include_images=True)
            
            print(f"        ✓ Saved to: {task_export_file.name}")
        
        print(f"\n✅ All annotations exported successfully!")
        print(f"\n📤 Share these files with collaborators:")
        for task in tasks:
            task_name = task.name.lower().replace(" ", "-")
            print(f"   - {task_name}-coco.zip")
        
        print(f"\n📝 Import Instructions:")
        print(f"   1. Open CVAT on their machine")
        print(f"   2. Create tasks with the same names")
        print(f"   3. For each task: Actions → Upload annotations")
        print(f"   4. Select COCO 1.0 format and upload the corresponding .zip")
        print(f"   5. Start annotating!")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export CVAT project for sharing")
    parser.add_argument("--host", default="http://localhost:8080")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--project-name", default="Buffelgrass Detection")
    parser.add_argument("--output-dir", default="./cvat/exports")
    
    args = parser.parse_args()
    
    success = export_project(
        host=args.host,
        username=args.username,
        password=args.password,
        project_name=args.project_name,
        output_dir=args.output_dir
    )
    
    sys.exit(0 if success else 1)

