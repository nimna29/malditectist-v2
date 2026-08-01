import pandas as pd

keep = set(pd.read_csv("keep_list.csv").filename)
obf = pd.read_csv("launchable_files_obfuscated.csv")

survived = set(obf.loc[obf.main_class_present, "filename"])
broken = sorted(keep - survived)

print(f"Keep List: {len(keep)}")
print(f"Still launchable after obfuscation: {len(keep & survived)}")
print(f"Broken by obfuscation: {len(broken)}")

for f in broken:
    print("  ", f)