# Main scraper module for Java file download

import os
import time
import json
import requests
from bs4 import BeautifulSoup
import re

from logger import get_logger
from manifest_checker import check_manifest
from get_latest import compare_version

log = get_logger("scraper")

# Config for the scraper
OUTPUT_ROOT = "JavaFiles"
PROGRESS_TRACK = "progress.json"
DELAY_SEC = 0.5
REQUEST_TIMEOUT = 30
REPO_BASE = "https://repo1.maven.org/maven2"
START_PATH = "" # Empty string to start from the root

# Output folders
FOLDERS = {
    "downloaded": os.path.join(OUTPUT_ROOT, "downloaded"),
    "selected": os.path.join(OUTPUT_ROOT, "selected"),
}

# Funtion to track progress
# It returns the saved status where the previous process stopped
def load_progress() -> dict:
    # loads the progress if the file exists
    # On resume it restore the queue and go to the exactly where the process stopped
    if os.path.exists(PROGRESS_TRACK):
        with open(PROGRESS_TRACK, "r") as f:
            data = json.load(f)
            log.info(f"Resuming: {len(data.get('queue', []))} directories left in queue")
            return data
        
    return {"queue": [START_PATH], "visited": [], 
            "downloaded": 0, "selected": 0}

# Function to save the progress
def save_progress(queue: list, visited: list, downloaded: int, selected: int):
    # Saves the current status into the json file
    with open(PROGRESS_TRACK, "w") as f:
        json.dump({
            "queue": queue,
            "visited": visited,
            "downloaded": downloaded,
            "selected": selected
        }, f, indent=2)

# Function to check whether file is already selected
def selected_already(filename: str) -> bool:
    selected_file = os.path.exists(os.path.join(FOLDERS["selected"], filename))
    return selected_file

# Function to fetch the download link from the html directory listing
def fetch_links(path: str) -> tuple[list[str], list[str]]:
    # Fetches the directory listing and parses the links to find subdirectories and jar files
    url = f"{REPO_BASE}/{path}" if path else REPO_BASE
    
    try:
        # Request the directory listing page
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        # Handle non 200 responses
        if response.status_code != 200:
            log.debug(f"Non 200 response: ({response.status_code}) | {url}")
            return [], []
        
        # Parse the HTML to find links
        soup = BeautifulSoup(response.text, "html.parser")
        links = [
            a["href"] for a in soup.find_all("a", href=True) # Get all href links
            if not a["href"].startswith("?") # skip Apache sort links
            and a["href"] != "../" # skip parent directory link
            and not a["href"].startswith("http") # skip absolute links
        ]
        
        # Separate subdirectories ending with "/" and files not ending with "/"
        subdirs = [link for link in links if link.endswith("/")]
        files   = [link for link in links if not link.endswith("/")]
        
        return subdirs, files
    
    except Exception as e:
        log.error(f"Failed to fetch directory listing: {url} | Error: {e}")
        return [], []

# Function to find if the folder is a version folder or not
def is_version_folder(files: list[str]) -> bool:
    # A version folder normally contains jar files directly inside it, without more subdirectories
    return any(f.endswith(".jar") for f in files)
        

# Function to donwload the files using the created url
# Retuns true and false based on success and fail to download
def download_file(url: str, down_path: str) -> bool:
    try:
        response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
        
        # Handle not found urls
        if response.status_code == 404:
            log.debug(f"404 Not Found: {url}")
            return False
        response.raise_for_status()
        
        with open(down_path, "wb") as f:
            # Writes the content in chunks to handle large files - 8192 bytes per time
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    
    except Exception as e:
        log.error(f"Failed to download: {url} | Error: {e}")
        return False

# Process the downloaded jar file and moves it into selected folder if its executable
def process_file(jar_path: str, filename: str) -> str:
    
    # Check the main class
    main_class = check_manifest(jar_path)
    # Remove the file if it doesn't have main class
    if not main_class:
        log.info(f" Not executable | Removing: {filename}")
        os.remove(jar_path)
        return "not_executable"
    
    log.info(f" Executable (Main-Class): {main_class}")
    
    # Move the executable file into selected folder
    selected_folder = FOLDERS["selected"]
    selected_path = os.path.join(selected_folder, filename)
    
    if os.path.exists(selected_path):
        log.info(f" Duplicate file in selected - Removing....")
        os.remove(jar_path)
    else:
        os.rename(jar_path, selected_path)
        log.info(f" File saved to the selected: {filename}")
    
    return "selected"

# Function to parse subdirectory into base name and version string
def parse_subdir_variants(name: str):
    match = re.match(r'^(.+?)([_\-])(\d[\d.]*)$', name.rstrip("/"))
    if match:
        base, sep, version = match.groups()
        return base, sep, version
    
    return None

# Function to group and get the latest sub directory
def filter_latest_subdirs(subdirs: list[str]) -> list[str]:
    groups = {} # (base, sep) into [(version_str, original_subdir)]
    ungrouped = [] # subdirs without version string
    
    # Loop the subdirs and group them by base name and separator
    for subdir in subdirs:
        parsed = parse_subdir_variants(subdir)
        
        # If the subdir has a version string group it using base name and separator
        if parsed:
            base, sep, version = parsed
            key = (base, sep)
            if key not in groups:
                groups[key] = []
            groups[key].append((version, subdir))
            
        else:
            ungrouped.append(subdir)
    
    result = list(ungrouped)
    
    # Loop the groups and keep only the highest version subdir
    for (base, sep), variants in groups.items():
        # If there is only one variant keep it as it is
        if len(variants) == 1:
            result.append(variants[0][1])
            
        else:
            # Sort the variants by version string and keep only the highest version
            try:
                variants.sort(key=lambda x: compare_version(x[0]), reverse=True)
            except Exception:
                pass # If sort fails keep original order
            
            # Keep the highest version and log the skipped variants
            highest = variants[0][1]
            skipped = len(variants) - 1 # Number of skipped variants
            
            log.debug(f" Variant filter (keeping): {highest.rstrip('/')} | Skipped {skipped} older variants")
            result.append(highest)

    return result


# Main function to run process
def run_process():
    # Create folders if they don't exist
    for folder in FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
    
    # Loads the previous progress
    progress = load_progress()
    queue = progress["queue"]
    visited = set(progress["visited"])
    downloaded = progress["downloaded"]
    selected = progress["selected"]
    
    # Counters for session
    session_downloaded = 0
    session_selected = 0
    session_not_exe = 0
    session_failed = 0
    
    # Startup banner
    log.info("#" * 50)
    log.info("MalDitectist V2 - Java File Downloader")
    log.info(f"Scraping from: {REPO_BASE}/")
    log.info(f"Queue size: {len(queue)} directories pending...")
    log.info("Press Ctrl + C to stop the script, and progress will be saved")
    log.info("#" * 50)
    
    try:
        # Loop through the pages until there are no more artifacts to process
        while queue:
            # Take the next directory from the front of the queue
            current_path = queue.pop(0)

            # Skip the path if already visited
            if current_path in visited:
                continue

            log.info(f" Scanning: /{current_path}")
            visited.add(current_path)
            
            # Fetch the subdirectories and files in the current path
            subdirs, files = fetch_links(current_path)

            # If there are no subdirs and no files just skip to the next path
            if not subdirs and not files:
                continue
            
            # Add the subdirs to the queue for more processing
            if is_version_folder(files):
                for filename in files:
                    if not filename.endswith(".jar"):
                        continue

                    # Skip all checksum and signature files
                    if any(filename.endswith(ext) for ext in
                            [".md5", ".sha1", ".sha256", ".asc"]):
                        continue
                
                    # Skip if the file already processed in a previous session
                    if selected_already(filename):
                        log.debug(f" Skipped (already processed): {filename}")
                        continue
                                    
                    # Build url and download file into the downloaded folder
                    file_path = f"{current_path}{filename}" if current_path else filename    
                    url = f"{REPO_BASE}/{file_path}"
                    temp_path = os.path.join(FOLDERS["downloaded"], filename)
                    
                    # Download the file and check the success of the download
                    log.info(f" Downloading: {filename}")
                    success = download_file(url, temp_path)
                    
                    if not success:
                        session_failed += 1
                        time.sleep(DELAY_SEC)
                        continue
                    
                    file_size = os.path.getsize(temp_path) // 1024
                    log.info(f" File Downloaded ({file_size} KB)")
                    session_downloaded += 1
                    downloaded += 1
                    
                    # Manifest check to select files
                    manifest_result = process_file(temp_path, filename)
                    
                    if manifest_result == "not_executable":
                        session_not_exe += 1
                    elif manifest_result == "selected":
                        session_selected += 1
                        selected += 1
                    
                    time.sleep(DELAY_SEC)
            
            # If it's not a version folder
            # Add the subdirs into the queue for more processing
            else:
                # Filter the subdirs to keep only the latest version variants
                filtered_subdirs = filter_latest_subdirs(subdirs)
                
                # Add the filtered subdirs into the queue for more processing
                for subdir in filtered_subdirs:
                    full_path = f"{current_path}{subdir}" if current_path else subdir
                    if full_path not in visited:
                        queue.append(full_path)
            
            # Save the progress after every dir
            save_progress(queue, list(visited), downloaded, selected)
    
    except KeyboardInterrupt:
        log.info("\nStopped by the user...")
        save_progress(queue, list(visited), downloaded, selected)
        log.info(f"Current progress saved...")
    
    log.info("\nNo more directories in queue... Process completed!")
    
    # Print a session summary
    log.info("#" * 50)
    log.info("--- Session Summary ---")
    log.info(f"> Downloaded: {session_downloaded}")
    log.info(f"> Selected: {session_selected}")
    log.info(f"> Not Executable: {session_not_exe}")
    log.info(f"> Failed: {session_failed}")
    log.info(f"> Total Selected: {selected}")
    log.info("#" * 50)


if __name__ == "__main__":
    run_process()