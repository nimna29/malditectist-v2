# Opcode Tracer module for MalDitectist V2
# Orchestrates the Docker + Intel PIN environment for each jar file
# Reason - Provide a clean new environment for each file
# Reads jar files from JavaFiles/selected-latest
# Write the output into the data/raw_traces

import os
import json
import subprocess
import sys
from pathlib import Path

# Add the parent directory to the sys.path to import the logger module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from data_collection.logger import get_logger

log = get_logger("tracer")

# I/O paths and files configs
INPUT_DIR = os.path.join("selected-latest")
OUTPUT_DIR = os.path.join("data", "raw_traces")
DOCKER_IMAGE = "malditectist-tracer"
PROGRESS_FILE = os.path.join("tracer_progress.json")

# PIN trace related settings
MAX_OPCODES = 1_000_000 # 1 million opcodes per jar file
TRACE_TIMEOUT = 90 # seconds before Docker kills the it's container

# Dokcer resource related settings
MEMORY_LIMIT = "1g" # 1GB RAM per container
CPU_LIMIT = "1.0" # 1 CPU core per container

# Optional setting to feed the generic input file to interact with the CLI programs
GENERIC_INPUT_FILE = os.path.join("src", "sandbox", "scripts", "generic_input.txt")
USE_GENERIC_INPUT = True # Toggle this to True and False to control the input


# Function to load the previous progress
def load_progress() -> dict:
    # load the tracer progress file if it exists
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            log.info(f"Resuming... {len(data.get('traced', []))} files already traced!")
            return data
        
    return {"traced": [], "failed": []}

# Function to save the current tracer progress
def save_progress(traced: list, failed: list):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"traced": traced, "failed": failed}, f, indent=2)

# Function to check the docker image
def check_docker_image() -> bool:
    # Check whether the Docker image already built
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True, text=True
        )
        return result.returncode == 0
    
    except FileNotFoundError:
        log.error("Docker is not installed or not in PATH, Please Check!")
        return False

# Function to trace a jar file
# Runs a jar file inside the Dokcer + Intel PIN tracer environment
def trace_jar(jar_path: str, output_path: str, input_file: str = None) -> bool:
    
    # Get the absolute paths for the jar file and output file
    jar_abs = os.path.abspath(jar_path)
    output_abs = os.path.abspath(output_path)
    output_filename = os.path.basename(output_abs)
    output_dir_abs = os.path.dirname(output_abs)
    
    # Run the Docker container with the resource limits and volume mounts
    cmd = [
        "docker", "run",
        "--rm",
        "--memory", MEMORY_LIMIT,
        "--cpus", CPU_LIMIT,
        "--network", "none",
        "-v", f"{jar_abs}:/trace/target.jar:ro",
        "-v", f"{output_dir_abs}:/trace/output",
    ]
    
    # Which is the run_trace.sh script with arguments inside the container
    container_args = [
        "/trace/target.jar",
        f"/trace/output/{output_filename}",
        str(MAX_OPCODES),
        "60",
    ]
    
    # If an input file is given it will mount and append as 5th arg
    if input_file and os.path.exists(input_file):
        input_abs = os.path.abspath(input_file)
        cmd += ["-v", f"{input_abs}:/trace/input.txt:ro"]
        container_args.append("/trace/input.txt")

    # Append the Docker image and container args to the cmd command
    cmd += [DOCKER_IMAGE] + container_args

    try:
        # Run the Docker container with a timeout and capture the output data
        result = subprocess.run(
            cmd,
            timeout = TRACE_TIMEOUT,
            capture_output = True,
            text = True
        )
        
        # Log the container output so failures are visible in console and logs
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log.info(f"  [container stdout] {line}")

        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log.error(f"  [container stderr] {line}")

        # Check if the output file exist and has content
        if os.path.exists(output_abs) and os.path.getsize(output_abs) > 0:
            # Count the number of opcodes captured and log it
            opcode_count = sum(1 for _ in open(output_abs))
            log.info(f"  Opcodes captured: {opcode_count:,}")
            return True
        
        else:
            log.warning(f"  Output file is empty or missing: {output_abs}")
            return False
    
    except subprocess.TimeoutExpired:
        log.warning(f" Docker timeout ({TRACE_TIMEOUT}s) and container killed")
        return False
    
    except Exception as e:
        log.error(f"  Docker run failed: {e}")
        return False
    

# Main fruntion to run the process
def run_process():
    
    # Check the env and paths
    if not os.path.exists(INPUT_DIR):
        log.error(f"Input folder not found: {INPUT_DIR}")
        log.error("Run the scraper.py and then run the organise_latest.py")
        return
    
    # Check if the docker image is exisit
    if not check_docker_image():
        log.error(f"Docker image '{DOCKER_IMAGE}' not found")
        log.error("Please build the Docker image first using the Dockerfile")
        log.error("Command(Inside sandbox): docker build -t malditectist-tracer .")
        return
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # load the jar files
    all_jars = sorted([
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".jar")
    ])
    
    if not all_jars:
        log.info("No jar files found in the selected-latest (Nothing to trace)")
        return
    
    # Load the previous progress
    progress = load_progress()
    traced = progress["traced"]
    failed = progress["failed"]
    traced_set = set(traced)
    
    # Counters for session
    success_count = 0
    failed_count  = 0
    skipped_count = 0

    # Startup banner
    log.info("#" * 50)
    log.info("MalDitectist V2 - Opcode Tracer")
    log.info(f"Input: {INPUT_DIR}/")
    log.info(f"Output: {OUTPUT_DIR}/")
    log.info(f"Total Files: {len(all_jars)}")
    log.info(f"Max Opcodes: {MAX_OPCODES:,} per file")
    log.info(f"Timeout: {TRACE_TIMEOUT}s per file")
    log.info(f"Docker Image: {DOCKER_IMAGE}")
    log.info("Press Ctrl+C to stop and the progress will be saved")
    log.info("#" * 50)

    # Run the tracing process for each jar file
    try:
        for index, jar_filename in enumerate(all_jars, start=1):
            
            # Set the full paths for the jar file and output trace file
            jar_path = os.path.join(INPUT_DIR, jar_filename)
            trace_name = jar_filename.replace(".jar", ".txt")
            output_path = os.path.join(OUTPUT_DIR, trace_name)
            
            log.info(f"\n[{index}/{len(all_jars)}] - {jar_filename}")
            
            # Skip if already traced in the previous session
            if jar_filename in traced_set:
                log.info(f" SKIPPED - Already traced")
                skipped_count += 1
                continue
            
            # Skip if the output file already exists with content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                log.info(f" SKIPPED - Trace file already have content")
                traced.append(jar_filename)
                traced_set.add(jar_filename)
                skipped_count += 1
                continue
            
            # Run the tracer to get success and pass generic input file is the setting is true
            input_file = GENERIC_INPUT_FILE if USE_GENERIC_INPUT else None
            success = trace_jar(jar_path, output_path, input_file=input_file)
            
            if success:
                traced.append(jar_filename)
                traced_set.add(jar_filename)
                success_count += 1
            
            else:
                failed.append(jar_filename)
                failed_count += 1
                # Remove empty output file if its created
                if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                    os.remove(output_path)
            
            # Save the progress after each file
            save_progress(traced, failed)
            
    except KeyboardInterrupt:
        log.info("\nStopped by the user...")
        save_progress(traced, failed)
        log.info(f"Current progress saved...")
        
    # Print a session summary
    log.info("#" * 50)
    log.info("--- Session Summary ---")
    log.info(f"> Traced Successfully: {success_count}")
    log.info(f"> Failed: {failed_count}")
    log.info(f"> Skipped: {skipped_count}")
    log.info(f"> Total Traced: {len(traced)}")
    log.info(f"> Output Directory: {os.path.abspath(OUTPUT_DIR)}/")
    log.info("#" * 50)


if __name__ == "__main__":
    run_process()

