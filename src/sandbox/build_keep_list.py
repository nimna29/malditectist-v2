# Reason for this script - the 260 files caontains some files that never executed program logic
# And files that cannot be obfuscated 
# Also some files that ran fine before but no longer launch after obfuscation
# All four environments must use the same file set for the model comparison

import os
import pandas as pd

LAUNCHABLE_CSV = "launchable_files_latest.csv"
EXIT_1_CSV = "exit_1_troubleshoot.csv"
MANIFEST_CSV = os.path.join("data", "manifest.csv")
OBFUSCATED_DIR = "selected-obfuscated"
OUT_CSV = "keep_list.csv"

RAN_KINDS = {"other", "runtime_exception", "ran_until_timeout"}

# Manually excluded these from the ran group after reading the first_line output from the log
# LinkageError happens while loading the main class so nothing executed from these files
DID_NOT_RUN = {
    "bgp-bmp-mock-2.0.0.jar",
    "bgp-testtool-2.0.0.jar",
    "avalon-phoenix-loader-4.0.4.jar",
    "loom-launcher-1.0-rc3.jar",
}

# After checking the check_keep_work these ran fine before obfuscation but not after
# Four report could not find or load main class because ProGuard renamed the class
# without rewriting the manifest, and two are corrupt partial writes left behind
# when both configs failed in middle
BROKEN_BY_OBFUSCATION = {
    "dtdparser-121.jar",
    "grammar-1.0.0-M01.jar",
    "grammar-M01.jar",
    "xom-1.4.5.jar",
    "izpack-standalone-compiler-3.7.2.jar",
    "javanettasks-1.0.29-jar-with-dependencies.jar",
}

launchable = pd.read_csv(LAUNCHABLE_CSV)
manifest = pd.read_csv(MANIFEST_CSV)
exit1 = pd.read_csv(EXIT_1_CSV)

df = launchable.merge(manifest[["filename", "exit_reason"]], on="filename")
exit1_kind = dict(zip(exit1.filename, exit1.kind))

# Decide per file whether the program actually executed
ran = set()
for row in df.itertuples():

    # A missing Main Class means the JVM never found an entry point
    if not row.main_class_present:
        continue

    # These never executed program logic even though the Main Class was present
    # Checked here so it applies to every exit reason and not only exit code 1
    if row.filename in DID_NOT_RUN:
        continue

    # Anything that did not exit with code 1 reached a normal end the size cap
    # or a program specific exit so it executed with a issue
    if row.exit_reason != "exit_code_1":
        ran.add(row.filename)
        continue

    # For the exit code 1 files use the exit_1 classification
    kind = exit1_kind.get(row.filename)
    if kind in RAN_KINDS:
        ran.add(row.filename)

obfuscated = {f for f in os.listdir(OBFUSCATED_DIR) if f.endswith(".jar")}

# Drop the files that survived both checks but broke during obfuscation
keep = sorted((ran & obfuscated) - BROKEN_BY_OBFUSCATION)

pd.DataFrame({"filename": keep}).to_csv(OUT_CSV, index=False)

print("#" * 50)
print("--- Keep List Summary ---")
print(f"> Total corpus: {len(df)}")
print(f"> Actually executed: {len(ran)}")
print(f"> Obfuscated successfully: {len(obfuscated)}")
print(f"> Ran but not obfuscated: {len(ran - obfuscated)}")
print(f"> Obfuscated but did not run: {len(obfuscated - ran)}")
print(f"> Broken by obfuscation: {len((ran & obfuscated) & BROKEN_BY_OBFUSCATION)}")
print("-" * 20)
print(f"> Final Keep List: {len(keep)}")
print(f"> Output: {os.path.abspath(OUT_CSV)}")
print("#" * 50)