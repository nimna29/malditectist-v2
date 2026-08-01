# exit_code_1_check.py - probe why files with a present Main-Class exit non-zero
import subprocess
import os
import pandas as pd

INPUT_ABS = os.path.abspath("selected-latest")
OUT_CSV = "exit_1_troubleshoot.csv"
TIMEOUT = 60

LANCH_CSV = pd.read_csv("launchable_files.csv")
MMANIFEST_CSV = pd.read_csv("data/manifest.csv")

df = LANCH_CSV.merge(MMANIFEST_CSV[["filename", "exit_reason"]], on = "filename")
targets = df[(df.main_class_present) & (df.exit_reason == "exit_code_1")].filename.tolist()

# Resume from a previous run
done = {}
if os.path.exists(OUT_CSV):
    prev = pd.read_csv(OUT_CSV)
    done = {r.filename: r._asdict() for r in prev.itertuples(index=False)}
    print(f"Resuming, {len(done)} already probed")

rows = list(done.values())

# Run each jar inside the same Docker image used for tracing
for i, jar in enumerate(targets, 1):
    if jar in done:
        continue
    print(f"[{i}/{len(targets)}] {jar}", flush=True)

    container = f"troubleshoot_{i}"
    
    try:
        run = subprocess.run(
            [
                "docker", "run", "--rm", "--name", container, "--entrypoint", "java",
                "-v", f"{INPUT_ABS}:/jars:ro",
                "malditectist-tracer", "-jar", f"/jars/{jar}"
            ],
            capture_output = True, text = True, timeout = TIMEOUT
        )
        
        out = (run.stdout + run.stderr).strip()
        code = run.returncode

    except subprocess.TimeoutExpired:
        # Still running after the timeout means it launched and is doing some work
        subprocess.run(["docker", "kill", container], capture_output = True, text = True)
        out, code = "", "timeout"

    first = out.splitlines()[0] if out else ""

    # Classify the failure so the files can be grouped into keep and drop later if needed
    if code == "timeout":
        kind = "ran_until_timeout"
        
    elif "NoClassDefFoundError" in out or "ClassNotFoundException" in out:
        kind = "missing_dependency"
        
    elif "Exception in thread" in out or "Caused by:" in out:
        kind = "runtime_exception"
        
    elif out == "":
        kind = "silent"
        
    else:
        kind = "other"

    rows.append({"filename": jar, "kind": kind, "exit_code": code, "first_line": first[:200]})

    # Save after every file so a crash never breake the progress
    pd.DataFrame(rows).to_csv(OUT_CSV, index = False)

res = pd.DataFrame(rows)
print()
print(res.kind.value_counts())