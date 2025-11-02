#!/usr/bin/env python3
"""
Automated CVAT project setup for buffelgrass detection.
Creates project, labels, task, and uploads images.
"""

import os
import sys
from pathlib import Path
from typing import List

try:
    from cvat_sdk import make_client
    from cvat_sdk.core.proxies.tasks import ResourceType
except ImportError:
    print("❌ CVAT SDK not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cvat-sdk"])
    from cvat_sdk import make_client
    from cvat_sdk.core.proxies.tasks import ResourceType


class CVATProjectSetup:
    """Automated CVAT project setup."""
    
    def __init__(
        self,
        host: str = "http://localhost:8080",
        username: str = None,
        password: str = None,
    ):
        """Initialize CVAT client."""
        self.host = host
        self.username = username or os.environ.get("CVAT_USERNAME")
        self.password = password or os.environ.get("CVAT_PASSWORD")
        self.client = None
        
    def connect(self):
        """Connect to CVAT instance."""
        if not self.username or not self.password:
            print("⚠️  No credentials provided.")
            print("Please set CVAT_USERNAME and CVAT_PASSWORD environment variables")
            print("or pass them as arguments.\n")
            self.username = input("CVAT Username: ")
            self.password = input("CVAT Password: ")
        
        print(f"🔗 Connecting to CVAT at {self.host}...")
        try:
            self.client = make_client(
                host=self.host,
                credentials=(self.username, self.password)
            )
            print(f"✅ Connected as {self.username}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def create_project(
        self,
        project_name: str = "Buffelgrass Detection",
        labels: List[str] = None,
    ):
        """Create CVAT project with labels."""
        if labels is None:
            labels = [
                "buffelgrass",
                "soil",
                "road",
                "building",
                "car",
                "tree_shrub",
                "cactus",
                "other_grass",
            ]
        
        print(f"\n📁 Creating project: {project_name}")
        
        # Check if project already exists
        projects = self.client.projects.list()
        for proj in projects:
            if proj.name == project_name:
                print(f"✅ Project '{project_name}' already exists (ID: {proj.id})")
                print(f"   Using existing project...")
                return proj.id
        
        # Create project with labels and distinct colors
        label_colors = {
            "buffelgrass": "#FF0000",    # Red - primary target
            "soil": "#8B4513",           # Brown
            "road": "#808080",           # Gray
            "building": "#800080",       # Purple
            "car": "#FFD700",            # Gold
            "tree_shrub": "#228B22",     # Forest green
            "cactus": "#00FF00",         # Bright green
            "other_grass": "#90EE90",    # Light green
        }
        
        label_specs = [
            {
                "name": label,
                "color": label_colors.get(label, "#FFFFFF"),  # Default to white if not specified
                "attributes": []
            }
            for label in labels
        ]
        
        try:
            project = self.client.projects.create({
                "name": project_name,
                "labels": label_specs
            })
            print(f"✅ Project created (ID: {project.id})")
            print(f"   Labels: {', '.join(labels)}")
            return project.id
        except Exception as e:
            print(f"❌ Failed to create project: {e}")
            return None
    
    def create_task(
        self,
        project_id: int,
        task_name: str = "Tumamoc 2023 Training Set",
        image_paths: List[str] = None,
        image_dir: str = None,
        image_quality: int = 70,
    ):
        """Create task and upload images."""
        print(f"\n📋 Creating task: {task_name}")
        
        # Collect image paths
        images = []
        if image_paths:
            images = [Path(p) for p in image_paths if Path(p).exists()]
        elif image_dir:
            image_dir = Path(image_dir)
            if image_dir.exists():
                # Support common image formats
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff', '*.bmp']:
                    images.extend(image_dir.glob(ext))
                    images.extend(image_dir.glob(ext.upper()))
        
        if not images:
            print("⚠️  No images provided or found.")
            print("Please specify image_paths or image_dir with images.")
            return None
        
        images = sorted(set(images))  # Remove duplicates
        print(f"   Found {len(images)} images to upload")
        
        if len(images) == 0:
            print("❌ No valid images found")
            return None
        
        # Show first few images
        print("   First images:")
        for img in images[:5]:
            print(f"     - {img.name}")
        if len(images) > 5:
            print(f"     ... and {len(images) - 5} more")
        
        # Create task
        try:
            task_spec = {
                "name": task_name,
                "project_id": project_id,
                "image_quality": image_quality,
            }
            
            print(f"\n⬆️  Uploading images (this may take a while)...")
            
            # Upload images
            task = self.client.tasks.create_from_data(
                spec=task_spec,
                resource_type=ResourceType.LOCAL,
                resources=[str(img) for img in images],
            )
            
            print(f"✅ Task created (ID: {task.id})")
            print(f"   {len(images)} images uploaded")
            print(f"\n🎨 Ready to annotate at: {self.host}/tasks/{task.id}")
            return task.id
            
        except Exception as e:
            print(f"❌ Failed to create task: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def setup_buffelgrass_project(
        self,
        image_dir: str = None,
        image_paths: List[str] = None,
    ):
        """Complete automated setup for buffelgrass project."""
        print("\n" + "=" * 60)
        print("🌾 Buffelgrass Detection - CVAT Project Setup")
        print("=" * 60)
        
        # Connect to CVAT
        if not self.connect():
            return False
        
        # Create project with comprehensive labels
        project_id = self.create_project(
            project_name="Buffelgrass Detection",
            labels=[
                "buffelgrass",
                "soil",
                "road",
                "building",
                "car",
                "tree_shrub",
                "cactus",
                "other_grass",
            ]
        )
        
        if not project_id:
            return False
        
        # Create task if images provided
        if image_dir or image_paths:
            task_id = self.create_task(
                project_id=project_id,
                task_name="Tumamoc 2023 Training Set",
                image_dir=image_dir,
                image_paths=image_paths,
            )
            
            if task_id:
                print("\n" + "=" * 60)
                print("✅ Setup Complete!")
                print("=" * 60)
                print(f"\n📍 Project: {self.host}/projects/{project_id}")
                print(f"📍 Task: {self.host}/tasks/{task_id}")
                print(f"\nYou can now start annotating! 🎉")
                return True
        else:
            print("\n" + "=" * 60)
            print("✅ Project Created!")
            print("=" * 60)
            print(f"\n📍 Project: {self.host}/projects/{project_id}")
            print(f"\nNext: Create a task and upload images via web UI")
            print(f"or run this script again with --image-dir")
            return True
        
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated CVAT setup for buffelgrass detection"
    )
    parser.add_argument(
        "--host",
        default="http://localhost:8080",
        help="CVAT host URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--username",
        help="CVAT username (or set CVAT_USERNAME env var)"
    )
    parser.add_argument(
        "--password",
        help="CVAT password (or set CVAT_PASSWORD env var)"
    )
    parser.add_argument(
        "--image-dir",
        help="Directory containing training images"
    )
    parser.add_argument(
        "--images",
        nargs="+",
        help="Specific image files to upload"
    )
    
    args = parser.parse_args()
    
    # Setup
    setup = CVATProjectSetup(
        host=args.host,
        username=args.username,
        password=args.password,
    )
    
    # Run setup
    success = setup.setup_buffelgrass_project(
        image_dir=args.image_dir,
        image_paths=args.images,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

