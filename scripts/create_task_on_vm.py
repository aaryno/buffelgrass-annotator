#!/usr/bin/env python3
"""
Create a single CVAT task on the VM with full debug output and progress monitoring.
Run this script ON the CVAT VM after installing cvat-sdk.

Usage:
    python3 create_task_on_vm.py --group ah --assignee aaryno

Requirements:
    pip install cvat-sdk==2.20.0
"""

import argparse
import glob
import time
from pathlib import Path

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType


def create_task_with_monitoring(
    cvat_url: str,
    username: str,
    password: str,
    group: str,
    assignee: str,
    project_id: int = 2,
):
    """Create a single CVAT task with full debug output."""
    
    print(f"\n{'='*80}")
    print(f"CREATING TASK FOR GROUP: {group.upper()}")
    print(f"{'='*80}\n")
    
    # Find images for this group
    image_dir = Path(f"/mnt/cvat-data/training_chips/{group}")
    if not image_dir.exists():
        print(f"❌ ERROR: Directory not found: {image_dir}")
        return False
    
    image_files = sorted(glob.glob(str(image_dir / "*.png")))
    if not image_files:
        print(f"❌ ERROR: No images found in {image_dir}")
        return False
    
    print(f"✅ Found {len(image_files)} images in {image_dir}")
    print(f"   First image: {Path(image_files[0]).name}")
    print(f"   Last image: {Path(image_files[-1]).name}")
    print()
    
    # Connect to CVAT
    print(f"🔌 Connecting to CVAT at {cvat_url}...")
    try:
        client = make_client(cvat_url, credentials=(username, password))
        print(f"✅ Connected successfully as {username}\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect: {e}")
        return False
    
    # Get assignee user
    print(f"👤 Looking up assignee: {assignee}...")
    try:
        users = client.users.list()
        assignee_user = None
        for user in users:
            if user.username == assignee:
                assignee_user = user
                break
        
        if assignee_user is None:
            print(f"❌ ERROR: User '{assignee}' not found")
            return False
        
        print(f"✅ Found user: {assignee_user.username} (ID: {assignee_user.id})\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to get users: {e}")
        return False
    
    # Create task
    task_name = f"Aaryn - {group.upper()}"
    print(f"📝 Creating task: '{task_name}'")
    print(f"   Project ID: {project_id}")
    print(f"   Assignee: {assignee_user.username}")
    print(f"   Images: {len(image_files)}")
    print()
    
    try:
        print("⏳ Calling client.tasks.create()...")
        task = client.tasks.create_from_data(
            spec={
                "name": task_name,
                "project_id": project_id,
                "assignee_id": assignee_user.id,
            },
            resource_type=ResourceType.LOCAL,
            resources=image_files,
            data_params={
                "image_quality": 70,
                "chunk_size": 72,
            },
        )
        print(f"✅ Task created with ID: {task.id}\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to create task: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Monitor task status
    print(f"{'='*80}")
    print(f"MONITORING TASK CREATION (ID: {task.id})")
    print(f"{'='*80}\n")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            # Refresh task data
            task.fetch()
            
            current_status = task.status.value if hasattr(task, 'status') else "unknown"
            
            # Print status updates
            if current_status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed:3d}s] Status: {current_status}")
                last_status = current_status
            
            # Check if complete
            if hasattr(task, 'status') and task.status.value == 'completed':
                print(f"\n✅ Task creation completed!")
                break
            
            # Check for errors
            if hasattr(task, 'status') and task.status.value == 'failed':
                print(f"\n❌ Task creation failed!")
                return False
            
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            time.sleep(2)
    else:
        print(f"\n⚠️  Timeout waiting for task completion (waited {max_wait}s)")
        print(f"   Current status: {last_status}")
        print(f"   Task may still be processing in background...")
    
    # Get final task details
    print(f"\n{'='*80}")
    print(f"FINAL TASK DETAILS")
    print(f"{'='*80}\n")
    
    try:
        task.fetch()
        print(f"Task ID: {task.id}")
        print(f"Task Name: {task.name}")
        print(f"Status: {task.status.value if hasattr(task, 'status') else 'unknown'}")
        print(f"Assignee ID: {task.assignee_id}")
        print(f"Project ID: {task.project_id}")
        
        # Check for jobs
        if hasattr(task, 'jobs'):
            jobs = list(task.get_jobs())
            print(f"\nJobs: {len(jobs)}")
            for job in jobs:
                print(f"  - Job ID: {job.id}, Status: {job.status.value if hasattr(job, 'status') else 'unknown'}")
        else:
            print(f"\nJobs: Unable to retrieve")
        
        print(f"\n✅ Task URL: {cvat_url}/tasks/{task.id}")
        
    except Exception as e:
        print(f"⚠️  Error retrieving final details: {e}")
    
    print(f"\n{'='*80}")
    print(f"TASK CREATION COMPLETE!")
    print(f"{'='*80}\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Create a single CVAT task on VM")
    parser.add_argument("--group", required=True, help="Group name (e.g., 'ah')")
    parser.add_argument("--assignee", required=True, help="Assignee username (e.g., 'aaryno')")
    parser.add_argument("--url", default="http://35.203.139.174:8080", help="CVAT URL (default: external IP)")
    parser.add_argument("--username", default="aaryno", help="CVAT admin username")
    parser.add_argument("--password", default="1976Weather1!", help="CVAT admin password")
    parser.add_argument("--project-id", type=int, default=2, help="Project ID (default: 2)")
    
    args = parser.parse_args()
    
    success = create_task_with_monitoring(
        cvat_url=args.url,
        username=args.username,
        password=args.password,
        group=args.group.lower(),
        assignee=args.assignee,
        project_id=args.project_id,
    )
    
    if success:
        print("✅ SUCCESS: Task created and ready for annotation!")
        return 0
    else:
        print("❌ FAILED: Task creation encountered errors")
        return 1


if __name__ == "__main__":
    exit(main())


