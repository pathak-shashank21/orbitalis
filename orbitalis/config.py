import os

# === [ Base path: full project root ] ===
# Current file is in: ~/Documents/dev/incubator/orbitalis/ssa_dashboard/
# We move one level up to reach the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# === [ Absolute path to conjunction risk CSVs ] ===
DATA_DIR = os.path.join(BASE_DIR, "output", "conjunction_events")

RISK_LEVELS = {
    "High": os.path.join(DATA_DIR, "high_risk_intervals.csv"),
    "Moderate": os.path.join(DATA_DIR, "moderate_risk_intervals.csv"),
    "Low": os.path.join(DATA_DIR, "low_risk_intervals.csv"),
    "Negligible": os.path.join(DATA_DIR, "negligible_risk_intervals.csv")
}

# === [ Cleaned orbits only for conjunction sats ] ===
PROPAGATED_CONJUNCTION_DIR = os.path.join(BASE_DIR, "output", "propagated_conjunction_sats")

# === [ Full orbit data (all EU sats) — optional/legacy ] ===
PROPAGATED_EU_DIR = os.path.join(BASE_DIR, "output", "propagated_eu_sats")
PROPAGATED_DEBRIS_DIR = os.path.join(BASE_DIR, "output", "propagated_debris")

# === [ Earth texture path for 3D rendering ] ===
TEXTURE_PATH = os.path.join(BASE_DIR, "visualization", "land_ocean_ice_2048.png")

# === [ Path Validators ] ===
def validate_paths():
    missing = []
    paths_to_check = {
        "DATA_DIR": DATA_DIR,
        "PROPAGATED_CONJUNCTION_DIR": PROPAGATED_CONJUNCTION_DIR,
        "TEXTURE_PATH": TEXTURE_PATH
    }
    for name, path in paths_to_check.items():
        if not os.path.exists(path):
            missing.append((name, path))
    return missing
