import os
import csv
import zipfile

INPUT_DIR = "selected-obfuscated"

# Function to scan and find which JAR truly have Main class
def main_class(path):
    try:
        # Open a JAR using zipfile 
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            mf = [n for n in names if n.upper() == "META-INF/MANIFEST.MF"]
            has_class = any(n.endswith(".class") for n in names)
            
            if not mf:
                return None, has_class, names
            
            # Read and decode the manifest text and ignore non decodable bytes
            content = z.open(mf[0]).read().decode("utf-8", "ignore")
            
            # manifest lines can wrap with a leading space - unfold it first
            content = content.replace("\r\n", "\n").replace("\n ", "")
            
            for line in content.splitlines():
                if line.lower().startswith("main-class:"):
                    return line.split(":", 1)[1].strip(), has_class, names
                
            return None, has_class, names
        
    except Exception as e:
        return f"ERROR:{e}", False, []

rows = []

for jar in sorted(os.listdir(INPUT_DIR)):
    if not jar.endswith(".jar"):
        continue
    
    mc, has_class, names = main_class(os.path.join(INPUT_DIR, jar))
    present = False
    
    # If a valid Main-Class was declared then check if the matching .class file exists
    if mc and not mc.startswith("ERROR"):
        present = (mc.replace(".", "/") + ".class") in names
    
    rows.append({
        "filename": jar,
        "main_class": mc or "",
        "has_any_class": has_class,
        "main_class_present": present,
    })


with open("launchable_files_obfuscated.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames = rows[0].keys())
    w.writeheader()
    w.writerows(rows)

n_noclass = sum(1 for r in rows if not r["has_any_class"])
n_missing = sum(1 for r in rows if r["has_any_class"] and not r["main_class_present"])
n_ok = sum(1 for r in rows if r["main_class_present"])

print(f"Total: {len(rows)}")
print(f"No .class files at all: {n_noclass}")
print(f"Main-Class declared but absent: {n_missing}")
print(f"Main-Class present in JAR: {n_ok}")