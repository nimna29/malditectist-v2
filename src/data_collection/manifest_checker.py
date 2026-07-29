import zipfile
from logger import get_logger

log = get_logger("manifest_checker")

# Function to check and identify the main class entry point
# Only executable have this
def check_manifest(jar_path: str) -> str | None:
    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            # Check if the MANIFEST.MF exists inside the jar zip
            manifest_entries = [
                name for name in jar.namelist()
                if name.upper() == "META-INF/MANIFEST.MF"
            ]
            
            if not manifest_entries:
                log.debug(f"No MANIFEST.MF found in {jar_path}")
                return None
            
            # Read the content of the manifest file
            with jar.open(manifest_entries[0]) as manifest_file:
                content = manifest_file.read().decode("utf-8", errors="ignore")
            
            # Parse key value pairs from the manifest file
            for line in content.splitlines():
                line = line.strip()
                # Check Main-Class entry that identifies the entry point of the program
                if line.lower().startswith("main-class:"):
                    main_class = line.split(":", 1)[1].strip()
                    log.debug(f"Main-Class found: {main_class} | {jar_path}")
                    return main_class
            
            log.debug(f"No Main-Class entry point in manifest: {jar_path}")
            return None
    
    except zipfile.BadZipFile:
        log.warning(f"zip/jar is not a valid file: {jar_path}")
        return None
    
    except Exception as e:
        log.error(f"Manifest check failed: {jar_path} | Error: {e}")
        return None