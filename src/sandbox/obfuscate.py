# Batch ProGuard obfuscation for E3 and E4 environments
# Generates one obfuscated JAR files set for both E3 (JIT) and E4 (no-JIT)
# Each JAR 1st try with the aggressive config first then with a no optimization config
# Because the optimizer aborts on JARs with an incomplete class hierarchy

import os
import csv
import subprocess
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from data_collection.logger import get_logger

log = get_logger("obfuscate")

# Path configuration
INPUT_DIR = os.path.join("selected-latest")
OUTPUT_DIR = os.path.join("selected-obfuscated")
MAPPING_DIR = os.path.join("proguard_mappings")
PROGUARD_JAR = os.path.join("proguard-7.6.1", "lib", "proguard.jar")
CONFIG_FILE = os.path.join("scripts", "proguard_obfuscation.pro")
FALLBACK_CONFIG = os.path.join("scripts", "proguard_fallback.pro")
PROGRESS_FILE = os.path.join("obfuscate_progress.json")

# Records which config each JAR was obfuscated with
# Needed for the writeup because a fallback file received a weaker transformation 
# than a main config file and that difference must be noted here for future use
CONFIG_USED_CSV = os.path.join("obfuscation_config_used.csv")

TIMEOUT_SEC = 900

# Java runtime module for -libraryjars Note: JDK 9+ uses jmods not rt.jar
JAVA_HOME = os.environ.get("JAVA_HOME", "/usr/lib/jvm/default-java")
JAVA_BASE = os.path.join(JAVA_HOME, "jmods", "java.base.jmod")


# Load and save progress to avoid already processed JARs
def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            log.info(f"Resuming... {len(data.get('done', []))} JARs Already Obfuscated")
            return data
        
    return {"done": [], "failed": []}


def save_progress(done: list, failed: list):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"done": done, "failed": failed}, f, indent=2)


# Save which config each file used
def save_config_used(config_used: dict):
    
    with open(CONFIG_USED_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "config"])
        writer.writeheader()
        
        for name, config in sorted(config_used.items()):
            writer.writerow({"filename": name, "config": config})


# Run ProGuard once with the given config file
# Separate out from obfuscate_jar so the same call can be reused for the fallback
# Returns the success state and a message which is either the size report or the error
def run_proguard(jar_name: str, config: str) -> tuple[bool, str]:
    in_path = os.path.join(INPUT_DIR, jar_name)
    out_path = os.path.join(OUTPUT_DIR, jar_name)
    map_path = os.path.join(MAPPING_DIR, jar_name.replace(".jar", ".map"))

    cmd = [
        "java", "-jar", PROGUARD_JAR,
        "@" + config,
        "-injars", in_path,
        "-outjars", out_path,
        "-libraryjars", JAVA_BASE,
        "-printmapping", map_path,
    ]

    try:
        result = subprocess.run(
            cmd, timeout=TIMEOUT_SEC, capture_output=True, text=True
        )

        # ProGuard writes its errors to stdout not stderr so both are joined here
        if result.returncode != 0:
            output = (result.stdout or "") + (result.stderr or "")
            
            # Keep only the last few lines thats where the real error msg sits
            tail = "\n".join(output.strip().splitlines()[-5:])
            return False, tail

        # Guard against silent fails where exit code is 0 but no JAR came out
        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            return False, f"Output JAR missing or empty: {out_path}"

        # Report the size shrink as a quick sanity check that obfuscation ran
        in_kb = os.path.getsize(in_path) / 1e3
        out_kb = os.path.getsize(out_path) / 1e3
        message = (f"{in_kb:.1f} KB -> {out_kb:.1f} KB "
                   f"({(1 - out_kb / in_kb) * 100:.1f}% smaller)")
        
        return True, message

    except subprocess.TimeoutExpired:
        return False, f"Timeout After {TIMEOUT_SEC}s"
    
    except Exception as e:
        return False, f"Failed: {e}"


# Obfuscate a single JAR falling back to the no optimization config on fails
# Returns the success state and the config name used so it can be recorded per file
def obfuscate_jar(jar_name: str) -> tuple[bool, str]:

    # First attempt with the aggressive optimization and shrinking config
    success, message = run_proguard(jar_name, CONFIG_FILE)
    
    if success:
        log.info(f" {message}")
        return True, "main"

    # The main config failed so retry without the optimization passes
    # This clears the incomplete class hierarchy errors 
    # While keeping the name obfuscation, shrinking and repackaging
    log.warning(f" Main config failed - Retrying without optimization")
    
    for line in message.splitlines():
        log.debug(f"   {line}")

    success, message = run_proguard(jar_name, FALLBACK_CONFIG)
    
    if success:
        log.info(f" [FALLBACK] {message}")
        return True, "fallback"

    # Both configs failed so this JAR cannot be obfuscated at all
    log.error(f" Both configs failed")
    
    for line in message.splitlines():
        log.error(f"  {line}")
        
    return False, "none"


# Main processing function to run the obfsucation on all JARs
def run_process():
    
    if not os.path.exists(PROGUARD_JAR):
        log.error(f"ProGuard not found: {PROGUARD_JAR}")
        return
    
    if not os.path.exists(CONFIG_FILE):
        log.error(f"Main config not found: {CONFIG_FILE}")
        return
    
    if not os.path.exists(FALLBACK_CONFIG):
        log.error(f"Fallback config not found: {FALLBACK_CONFIG}")
        return
    
    if not os.path.exists(JAVA_BASE):
        log.error(f"Java base module not found: {JAVA_BASE}")
        log.error("Set JAVA_HOME correctly (JDK 9+ needed for jmods)")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MAPPING_DIR, exist_ok=True)

    all_jars = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".jar")])
    if not all_jars:
        log.info("No JAR files found in selected-latest")
        return

    progress = load_progress()
    done, failed = progress["done"], progress["failed"]
    done_set = set(done)
    
    # Tracks the config each successful file used across the session
    config_used = {}

    log.info("#" * 50)
    log.info("MalDitectist V2 - ProGuard Obfuscation (E3/E4 input)")
    log.info(f"Input: {INPUT_DIR}/")
    log.info(f"Output: {OUTPUT_DIR}/")
    log.info(f"Total Files: {len(all_jars)}")
    log.info(f"Main Config: {CONFIG_FILE}")
    log.info(f"Fallback Config: {FALLBACK_CONFIG}")
    log.info("#" * 50)

    ok = fail = skip = 0
    fallback_count = 0

    try:
        for i, jar_name in enumerate(all_jars, 1):
            log.info(f"\n[{i}/{len(all_jars)}] - {jar_name}")

            if jar_name in done_set:
                log.info("  SKIPPED - Already obfuscated")
                skip += 1
                continue

            success, config_name = obfuscate_jar(jar_name)

            if success:
                done.append(jar_name)
                done_set.add(jar_name)
                config_used[jar_name] = config_name
                ok += 1
                
                if config_name == "fallback":
                    fallback_count += 1
                
            else:
                failed.append(jar_name)
                fail += 1

            save_progress(done, failed)
            save_config_used(config_used)

    except KeyboardInterrupt:
        log.info("\nStopped by the user...")
        save_progress(done, failed)
        save_config_used(config_used)

    log.info("#" * 50)
    log.info("--- Session Summary ---")
    log.info(f"> Obfuscated: {ok}")
    log.info(f"> Used Main Config: {ok - fallback_count}")
    log.info(f"> Used Fallback Config: {fallback_count}")
    log.info(f"> Failed: {fail}")
    log.info(f"> Skipped: {skip}")
    log.info(f"> Output: {os.path.abspath(OUTPUT_DIR)}/")
    log.info("#" * 50)

    if failed:
        log.warning(f"Failed JARs ({len(failed)}): {failed}")


if __name__ == "__main__":
    run_process()