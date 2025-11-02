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
    
    print(f"\n📦 Exporting project...")
    print(f"   Output: {export_file}")
    
    try:
        # Export project (includes tasks, annotations, etc.)
        client.projects.retrieve(project.id).export_dataset(
            format_name="CVAT 1.1",
            filename=str(export_file)
        )
        
        print(f"✅ Project exported successfully!")
        print(f"\n📤 Share this file with collaborators:")
        print(f"   {export_file}")
        print(f"\n📝 Import Instructions:")
        print(f"   1. Open CVAT on their machine")
        print(f"   2. Go to Projects → Import")
        print(f"   3. Upload: {export_file.name}")
        print(f"   4. Start annotating!")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
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

