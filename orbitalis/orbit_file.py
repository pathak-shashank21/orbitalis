import pandas as pd
import os
import shutil
import re

# === Paths ===
risk_files_dir = "output/conjunction_events"
orbit_source_dir = "output/propagated_eu_sats"
orbit_target_dir = "output/propagated_conjunction_sats"
os.makedirs(orbit_target_dir, exist_ok=True)

# === Risk files to check ===
risk_files = [
    "high_risk_intervals.csv",
    "moderate_risk_intervals.csv",
    "low_risk_intervals.csv",
    "negligible_risk_intervals.csv"
]

# === Normalize for matching ===
def normalize(name):
    return re.sub(r"[^A-Z0-9]", "", name.upper())

# === safe_filename used in Streamlit ===
def safe_filename(name):
    return name.replace(" ", "_").upper()

# === Extract unique satellite_1 names from conjunctions ===
sat_names = set()
for file in risk_files:
    path = os.path.join(risk_files_dir, file)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if "satellite_1" in df.columns:
                sat_names.update(df["satellite_1"].dropna().unique())
            else:
                print(f"⚠️ File missing 'satellite_1': {file}")
        except Exception as e:
            print(f"⚠️ Could not read {file}: {e}")
    else:
        print(f"⚠️ Missing: {path}")

# === Copy and rename to match Streamlit's safe_filename() ===
copied = 0
for sat in sorted(sat_names):
    norm_sat = normalize(sat)
    target_name = safe_filename(sat) + ".csv"
    found = False

    for f in os.listdir(orbit_source_dir):
        fname_base = os.path.splitext(f)[0]
        if norm_sat in normalize(fname_base):  # flexible matching
            src = os.path.join(orbit_source_dir, f)
            dst = os.path.join(orbit_target_dir, target_name)
            shutil.copyfile(src, dst)
            copied += 1
            found = True
            break

    if not found:
        print(f"❌ Orbit file not found for: {sat} → {target_name}")

print(f"\n✅ Copied {copied} orbit files to: {orbit_target_dir}")
