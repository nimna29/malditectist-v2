# Script to organize the selected files and get a copy of latest files
# Need to run this after scraper donwloaded jar files

import os
import re
import shutil
from packaging.version import Version, InvalidVersion

from logger import get_logger

log = get_logger("get_latest")

# # Config for the script
OUTPUT_ROOT = "JavaFiles"
SELECTED_DIR = os.path.join(OUTPUT_ROOT, "selected")
LATEST_DIR = os.path.join(OUTPUT_ROOT, "selected-latest")

# Function to parse the selected jar files version using filename
def parse_version(filename: str) -> tuple[str, str | None]:
    # Parses the filename to extract artifact and version information
    name = filename.removesuffix(".jar")
    parts = name.split("-")
    
    # Look for the first part that starts with a digit
    # Which usually indicates the start of the version
    for i, part in enumerate(parts):
        if part and part[0].isdigit():
            artifact = "-".join(parts[:i]) # Artifact is the part before the version
            version = "-".join(parts[i:]) # Version is the part starting from the first digit
            return artifact, version
    
    # If no version found, function return full name with no version   
    return name, None

# Function to compare 2 version strings
def compare_version(version_str: str) -> Version:
    try:
        # Try to parse the version string using packaging
        return Version(version_str)
    except InvalidVersion:
        # For non standard versions extract rest of the numeric parts
        numeric = re.match(r"[\d.]+", version_str)
        # If no numeric part found fallback to 0 to avoid errors
        fallback = numeric.group(0) if numeric else "0"
        # Try to parse the fallback version if it also fails return 0
        try:
            return Version(fallback)
        except InvalidVersion:
            return Version("0")
        
# Function to get the latest versions
def get_latest():
    # 1st check the selected folder and if it has files
    if not os.path.exists(SELECTED_DIR):
        log.error(f"The selected folder not found: {SELECTED_DIR}")
        log.error("Please run the scraper to download files!")
        return
    
    # Get all the jar files inside the selected folder
    all_jars = [f for f in os.listdir(SELECTED_DIR) if f.endswith(".jar")]
    
    if not all_jars:
        log.info("No jar files found in the selected folder!")
        return
    
    # Create the selected-latest folder
    os.makedirs(LATEST_DIR, exist_ok=True)
    
    # Startup banner
    log.info("#" * 50)
    log.info("MalDitectist V2 - Get Latest Versions")
    log.info(f"Files Source: {SELECTED_DIR}")
    log.info(f"Files Destination: {LATEST_DIR}")
    log.info(f"Total Files: {len(all_jars)}")
    log.info("#" * 50)
    
    # Groups the artifact using their file names
    artifact_groups: dict[str, list[tuple[str | None, str]]] = {}
    
    # Loop all the jar files and group them by artifact name
    for jar in all_jars:
        artifact, version = parse_version(jar)
        if artifact not in artifact_groups:
            artifact_groups[artifact] = []
        artifact_groups[artifact].append((version, jar))
    
    log.info(f"No of unique artifacts: {len(artifact_groups)}")
    
    # Clear the selected-latest folder if it exists and recreate with the latest versions
    old_latest = os.listdir(LATEST_DIR)
    
    # Loop each artifact group and find the latest version
    if old_latest:
        log.info(f"Clearing {len(old_latest)} existing files from the selected-latest")
        for f in old_latest:
            os.remove(os.path.join(LATEST_DIR, f))
    
    copied = 0
    all_kept = 0
    
    for artifact, versions in artifact_groups.items():
        
        # Only one version allowed to copy
        if len(versions) == 1:
            _, jar = versions[0] # Get the only version available
            shutil.copy2(
                os.path.join(SELECTED_DIR, jar),
                os.path.join(LATEST_DIR, jar)
            )
            copied += 1
            
        else:
            # Mutiple versions for difficult version numbers
            # Get the versions that is able to parse version numbers
            versioned = [(v, j) for v, j in versions if v is not None]
            
            # Get the versions that is not able to parse version numbers
            no_version = [(v, j) for v, j in versions if v is None]
            
            if versioned:
                try:
                    # Sort in descending order to get the highest
                    versioned.sort(key=lambda x: compare_version(x[0]), reverse=True)
                    latest_ver, latest_jar = versioned[0] # Get the latest version
                    shutil.copy2(
                        os.path.join(SELECTED_DIR, latest_jar),
                        os.path.join(LATEST_DIR, latest_jar)
                    )
                    log.info(f" Latest Version: {latest_jar} ({len(versioned)} versions found)")
                    copied += 1
                
                except Exception as e:
                    # Version compare failed and copy all files
                    log.warning(f" Version compare failed for: {artifact} | Error: {e}")
                    
                    for _, jar in versions:
                        shutil.copy2(
                        os.path.join(SELECTED_DIR, jar),
                        os.path.join(LATEST_DIR, jar)
                    )
                    all_kept += 1
            
            # Copy any files that doesnt have correct version no
            for _, jar in no_version:
                shutil.copy2(
                    os.path.join(SELECTED_DIR, jar),
                    os.path.join(LATEST_DIR, jar)
                )
    
    # Print a session summary
    total_latest = len(os.listdir(LATEST_DIR))
    log.info("#" * 50)
    log.info("--- Session Summary ---")
    log.info(f"> Artifacts Processed: {len(artifact_groups)}")
    log.info(f"> Latest Versions: {copied}")
    log.info(f"> All Kept Files: {all_kept}")
    log.info(f"> Total Files in selected-latest: {total_latest}")
    log.info("#" * 50)


if __name__ == "__main__":
    get_latest()