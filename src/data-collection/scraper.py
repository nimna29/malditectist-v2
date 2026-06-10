# Main scraper module for Java file download

import os
import time
import json
import requests

from logger import get_logger
from manifest_checker import check_manifest

log = get_logger("scraper")

# Config for the scraper
OUTPUT_ROOT = "JavaFiles"
PROGRESS_TRACK = "progress.json"
BATCH_SIZE = 200
DELAY_SEC = 1.0
REQUEST_TIMEOUT = 30
SEARCH_API = "https://search.maven.org/solrsearch/select"
REPO_BASE = "https://repo1.maven.org/maven2"

# Output folders
FOLDERS = {
    "downloaded": os.path.join(OUTPUT_ROOT, "downloaded"),
    "selected": os.path.join(OUTPUT_ROOT, "selected"),
}

# Funtion to track progress
# It returns the saved status where the previous process stopped
def load_progress() -> dict:
    # loads the progress if the file exists
    if os.path.exists(PROGRESS_TRACK):
        with open(PROGRESS_TRACK, "r") as f:
            data = json.load(f)
            log.info(f"Resuming from page {data.get('page', 0)} "
                    f"(and start offset {data.get('start', 0)})")
            return data
    return {"page": 1, "start": 0, "total_found": 0}

# Function to save the progress
def save_progress(page: int, start: int, total_found: int):
    # Saves the current status into the json file
    with open(PROGRESS_TRACK, "w") as f:
        json.dump({
            "page": page,
            "start": start,
            "total_found": total_found
        }, f, indent=2)

# Function to check whether file is already selected
def selected_already(filename: str) -> bool:
    selected_file = os.path.exists(os.path.join(FOLDERS["selected"], filename))
    return selected_file

# Function to search batch of artifacts using maven central search API
# Returns a tuple of artifacts docs and num of available results
def fetch_batch(start: int) -> tuple[list[dict], int]:
    """
    API Endpoint: GET https://search.maven.org/solrsearch/select
    Params: q=*&rows=200&start={offset}&wt=json
    API Docs: https://central.sonatype.org/search/rest-api-guide
    """
    
    params = {
        "q": "p:jar",
        "rows": BATCH_SIZE,
        "start": start,
        "wt": "json"
    }
    
    try:
        response = requests.get(SEARCH_API, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        body = response.json().get("response", {})
        docs = body.get("docs", [])
        total = body.get("numFound", 0)
        return docs, total
    
    except Exception as e:
        log.error(f"Search API request failed, start = {start} | Error: {e} ")
        return [], 0

# Function to create direct donwload url for jar file
def download_url(group_id: str, artifact_id: str, version: str) -> str:
    """
    URL pattern based on Maven Repository Layout
    https://repo1.maven.org/maven2/{groupId or path}/{artifactId}/{version}/{artifactId}-{version}.jar
    
    ${groupId as directory} is the groupId with . replaced by / 
    Example: org/apache/maven
    """
    
    group_path = group_id.replace(".", "/")
    filename = f"{artifact_id}-{version}.jar"
    url = f"{REPO_BASE}/{group_path}/{artifact_id}/{version}/{filename}"
    
    return url

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
    
    if os.path.exists(selected_folder):
        log.info(f" Duplicate file in selected - Removing....")
        os.remove(jar_path)
    else:
        os.rename(jar_path, selected_path)
        log.info(f" File saved to the selected: {filename}")
    
    return "selected"

# Main function to run process
def run_process():
    # Create folders if they don't exist
    for folder in FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
    
    # Loads the previous progress
    progress = load_progress()
    page = progress["page"]
    start = progress["start"]
    
    # Counters for session
    session_downloaded = 0
    session_selected = 0
    session_skipped = 0
    session_not_exe = 0
    session_failed = 0
    
    # Startup banner
    log.info("#" * 50)
    log.info("MalDitectist V2 - Java File Downloader")
    log.info(f"Batch size: {BATCH_SIZE} artifacts per page")
    log.info(f"Starting from page {page} and offset = {start}")
    log.info("Press Ctrl + C to stop the script, and progress will be saved")
    log.info("#" * 50)
    
    try:
        # Loop through the pages until there are no more artifacts to process
        while True:
            log.info(f"\n --- Page: {page} and Offset {start} ---")
            
            docs, total = fetch_batch(start)
            
            if not docs:
                log.info("No more artifacts found, ending the process.")
                break
            
            # Log the number of artifacts fetched and total available
            log.info(f"Fetched {len(docs)} artifacts "
                        f"Total available: {total:,}")
            
            # Process each artifact in the fetched batch
            for doc in docs:
                group_id = doc.get("g", "")
                artifact_id = doc.get("a", "")
                version = doc.get("latestVersion", "")
                
                if not group_id or not artifact_id or not version:
                    session_failed += 1
                    continue
                
                label = f"{group_id}:{artifact_id}"
                filename = f"{artifact_id}-{version}.jar"
                
                # Skip if the file already processed in a previous session
                if selected_already(filename):
                    log.debug(f" Skipped (already processed): {label}")
                    session_failed += 1
                    continue
                
                log.info(f" {label} v{version}")
                
                # Build url and download file into the downloaded folder
                url = download_url(group_id, artifact_id, version)
                temp_path = os.path.join(FOLDERS["downloaded"], filename)
                
                # Download the file and check the success of the download
                success = download_file(url, temp_path)
                if not success:
                    session_failed += 1
                    time.sleep(DELAY_SEC)
                    continue
                
                file_size = os.path.getsize(temp_path) // 1024
                log.info(f" File Downloaded ({file_size} KB)")
                session_downloaded += 1
                
                # Manifest check to select files
                mainfest_result = process_file(temp_path, filename)
                
                if mainfest_result == "not_executable":
                    session_not_exe += 1
                elif mainfest_result == "selected":
                    session_selected += 1
                
                time.sleep(DELAY_SEC)
            
            # Save the progress after each full page
            start += BATCH_SIZE
            page += 1
            save_progress(page, start, total)
            log.info(f"Progress Saved | Next will be start at page {page}")
            
            # Stop if the scrip gone through every artifact
            if start >= total:
                log.info("All available articats processed...")
                break
    
    except KeyboardInterrupt:
        log.info("\nStopped by the user...")
        save_progress(page, start, 0)
        log.info(f"Current progress saved...")
    
    # Print a session summary
    log.info("#" * 50)
    log.info("--- Session Summary ---")
    log.info(f"> Downloaded: {session_downloaded}")
    log.info(f"> Selected: {session_selected}")
    log.info(f"> Not Executable: {session_not_exe}")
    log.info(f"> Skipped Files: {session_skipped}")
    log.info(f"> Failed: {session_failed}")
    log.info(f"> Next Offset: {start}")
    log.info("#" * 50)


if __name__ == "__main__":
    run_process()