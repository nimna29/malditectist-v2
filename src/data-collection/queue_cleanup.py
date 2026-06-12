# One time script to clean the existing queue in progress.json file

import os
import json
import shutil
import re

from logger import get_logger
from scraper import filter_latest_subdirs

log = get_logger("queue_cleanup")

PROGRESS_FILE = "progress.json"
PROGRESS_BACKUP = "progress.json.backup"

def main():
    # Check if the progress file exists
    if not os.path.exists(PROGRESS_FILE):
        log.error(f"Progress file not found: {PROGRESS_FILE}")
        return
    
    # load the current progress file
    with open(PROGRESS_FILE, "r") as f:
        progress = json.load(f)
    
    # Variables to track the file details
    queue = progress.get("queue", [])
    visited = progress.get("visited", [])
    downloaded = progress.get("downloaded", 0)
    selected = progress.get("selected", 0)
    
    # Startup banner
    log.info("#" * 50)
    log.info("MalDitectist V2 - Queue Cleaner")
    log.info(f"Queue size before cleanup: {len(queue):,}")
    log.info(f"Visited entries: {len(visited):,}")
    log.info("#" * 50)
    
    # Make a backup of the original progress file before making any changes
    shutil.copy2(PROGRESS_FILE, PROGRESS_BACKUP)
    log.info(f"Backup of the original progress: {PROGRESS_BACKUP}")
    
    # Apply the filters into the queue
    # Group the queue entries by their parent directory
    parent_groups: dict[str, list[str]] = {}
    
    for entry in queue:
        # Parent is the everything up to the last slash 
        # Split using the last slash to separate parent and name
        parts = entry.rstrip("/").rsplit("/", 1)
        
        # If there is a parent directory it will be parts, if not it is an empty string
        parent = parts[0] + "/" if len(parts) > 1 else ""
        
        # The name is the last segment of the path
        name = parts[-1] + "/"
        
        if parent not in parent_groups:
            parent_groups[parent] = []
        
        parent_groups[parent].append(name)
        
    # Filter each parent groups and recreate the queue
    filtered_queue = []
    total_skipped = 0
    
    # Loop each parent group and filter the siblings to keep only the latest version
    for parent, siblings in parent_groups.items():
        filtered = filter_latest_subdirs(siblings)
        skipped = len(siblings) - len(filtered)
        total_skipped += skipped
        
        for entry in filtered:
            filtered_queue.append(f"{parent}{entry}" if parent else entry)

    log.info(f"Queue size after cleanup: {len(filtered_queue):,}")
    log.info(f"Total entries skipped: {total_skipped:,}")
    
    # Update the progress file with new details
    with open(PROGRESS_FILE, "w") as f:
        json.dump({
            "queue": filtered_queue,
            "visited": visited,
            "downloaded": downloaded,
            "selected": selected
        }, f, indent=2)
    
    log.info(f"Cleaned progress file saved to: {PROGRESS_FILE}")
    log.info("Cleanup Process Completed!")

if __name__ == "__main__":
    main()