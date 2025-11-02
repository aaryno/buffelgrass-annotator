#!/usr/bin/env python3
"""
Create all 20 CVAT tasks from the VM where the images are stored.
This is MUCH faster than uploading from local machine.
"""

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType
from pathlib import Path
import time

# CVAT connection
HOST = "http://localhost:8080"
USERNAME = "aaryno"
PASSWORD = "1976Weather1!"

# Task definitions: (group, annotator_name, username)
TASKS = [
    # Aaryn's tasks
    ("ah", "Aaryn", "aaryno"),
    ("bt", "Aaryn", "aaryno"),
    ("dx", "Aaryn", "aaryno"),
    ("ej", "Aaryn", "aaryno"),
    ("ev", "Aaryn", "aaryno"),
    # Kim's tasks
    ("gx", "Kim", "kim"),
    ("il", "Kim", "kim"),
    ("kg", "Kim", "kim"),
    ("lt", "Kim", "kim"),
    ("ni", "Kim", "kim"),
    # Stephen's tasks
    ("pd", "Stephen", "stephen"),
    ("ra", "Stephen", "stephen"),
    ("rb", "Stephen", "stephen"),
    ("tr", "Stephen", "stephen"),
    ("vc", "Stephen", "stephen"),
    # Kaitlyn's tasks
    ("vq", "Kaitlyn", "kaitlyn"),
    ("vt", "Kaitlyn", "kaitlyn"),
    ("wk", "Kaitlyn", "kaitlyn"),
    ("xi", "Kaitlyn", "kaitlyn"),
    ("yo", "Kaitlyn", "kaitlyn"),
]

def main():
    print("=" * 70)
    print("Creating 20 CVAT Tasks from VM")
    print("=" * 70)
    
    # Connect to CVAT
    print("\n[1/3] Connecting to CVAT...")
    client = make_client(host=HOST, credentials=(USERNAME, PASSWORD))
    print("      Connected!")
    
    # Get project and users
    print("\n[2/3] Getting project and users...")
    projects = client.projects.list()
    project = [p for p in projects if p.name == "Buffelgrass Detection - 3 Class"][0]
    
    users_list = client.users.list()
    users = {u.username: u for u in users_list}
    
    print(f"      Project ID: {project.id}")
    print(f"      Users: {', '.join(users.keys())}")
    
    # Create all tasks
    print(f"\n[3/3] Creating {len(TASKS)} tasks...")
    print("=" * 70)
    
    results = []
    total_start = time.time()
    
    for idx, (group, annotator_name, username) in enumerate(TASKS, 1):
        # Get image files
        image_dir = Path(f"/mnt/cvat-data/training_chips/{group}")
        image_files = sorted(image_dir.glob("*.png"))
        
        if not image_files:
            print(f"\n[{idx:2d}/20] ❌ {group.upper()}: No images found!")
            continue
        
        print(f"\n[{idx:2d}/20] {annotator_name} - {group.upper()}")
        print(f"        Images: {len(image_files)}")
        print(f"        Uploading...", end=" ", flush=True)
        
        start_time = time.time()
        
        try:
            task = client.tasks.create_from_data(
                spec={
                    "name": f"{annotator_name} - {group.upper()}",
                    "project_id": project.id,
                    "assignee_id": users[username].id,
                },
                resource_type=ResourceType.LOCAL,
                resources=[str(f) for f in image_files],
                data_params={
                    "image_quality": 70,
                },
                status_check_period=2,
            )
            
            elapsed = time.time() - start_time
            
            print(f"✅ Done in {elapsed:.1f}s")
            print(f"        Task ID: {task.id}, Size: {task.size}")
            
            results.append({
                "group": group,
                "task_id": task.id,
                "images": task.size,
                "time": elapsed,
                "success": True
            })
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Failed in {elapsed:.1f}s")
            print(f"        Error: {str(e)[:100]}")
            
            results.append({
                "group": group,
                "task_id": None,
                "images": len(image_files),
                "time": elapsed,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    total_elapsed = time.time() - total_start
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_images = sum(r["images"] for r in successful)
        print(f"\n✅ Created {len(successful)} tasks with {total_images} images total")
        print("\nTask IDs:")
        for r in successful:
            print(f"  {r['group']}: Task {r['task_id']} ({r['images']} images)")
    
    if failed:
        print(f"\n❌ Failed tasks:")
        for r in failed:
            print(f"  {r['group']}: {r.get('error', 'Unknown error')[:80]}")
    
    print("\n🎯 View tasks: http://35.203.139.174:8080/tasks")
    print("=" * 70)

if __name__ == "__main__":
    main()


