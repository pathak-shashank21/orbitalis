
import os
import time
import argparse
import logging
import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import glob
from pathlib import Path

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.DEBUG)

from pathlib import Path

def load_satellite_data(folder_path):
    def fix_name(raw_name):
        name = Path(raw_name).stem
        if name.endswith("_mc"):
            name = name[:-3]
        name = name.replace("_", " ").strip()
        return name.upper()

    sat_data = {}
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    for file in csv_files:
        try:
            df = pd.read_csv(file, parse_dates=["timestamp"])
            if "timestamp" not in df.columns:
                print(f"⚠️ Skipping {file} — missing 'timestamp' column.")
                continue

            if "name" in df.columns:
                name = str(df["name"].iloc[0])
            else:
                name = fix_name(file)  # ✅ Always clean fallback names

            # ✅ Clean both TLE and fallback names uniformly
            name = fix_name(name)

            sat_data[name] = df
        except Exception as e:
            print(f"⚠️ Error reading {file}: {e}")
            continue

    if not sat_data:
        raise ValueError(f"No valid satellite CSVs found in {folder_path}")
    return sat_data



def classify_risk(miss_km):
    if miss_km <= 60:
        return "HIGH"
    elif miss_km <= 100:
        return "MODERATE"
    
    elif miss_km <= 200:
        return "LOW"
    elif miss_km <= 500:
        return "NEGLIGIBLE"
    else:
        return None

def detect_conjunctions(eu_data, debris_data, threshold_km=200, log_every=10):
    all_events = []
    timestamps = eu_data[list(eu_data.keys())[0]]["timestamp"].drop_duplicates().values
    logging.info(f"🧪 First timestamp: {timestamps[0]}")
    logging.info(f"🛰️ EU sample: {list(eu_data.keys())[:3]}")
    logging.info(f"🛰️ Debris sample: {list(debris_data.keys())[:3]}")
    logging.info(f"📅 Checking {len(timestamps)} timestamps...")

    for i, t in enumerate(timestamps):
        if i % log_every == 0:
            logging.info(f"⏳ Progress: {i}/{len(timestamps)}")

        debris_pos, debris_names = [], []
        debris_rows = []

        for name, df in debris_data.items():
            row = df.loc[np.isclose(df["timestamp"].astype(np.int64), t.astype(np.int64), atol=1_000_000)]
            if not row.empty:
                pos = row[["x_km", "y_km", "z_km"]].values[0]
                try:
                    pos = pos.astype(float)
                except:
                    continue
                if not np.any(np.isnan(pos)):
                    debris_pos.append(pos)
                    debris_names.append(name)
                    debris_rows.append(row.iloc[0])


        if not debris_pos:
            continue

        debris_kdtree = KDTree(debris_pos)

        for eu_name, eu_df in eu_data.items():
            row = eu_df.loc[np.isclose(eu_df["timestamp"].astype(np.int64), t.astype(np.int64), atol=1_000_000)]
            if row.empty:
                continue

            eu_row = row.iloc[0]
            pos = row[["x_km", "y_km", "z_km"]].values[0]
            try:
                pos = pos.astype(float)
            except:
                continue
            if np.any(np.isnan(pos)):
                continue


            dists, indices = debris_kdtree.query(pos, k=min(5, len(debris_pos)))
            if np.isscalar(dists):
                dists, indices = [dists], [indices]

            for dist, idx in zip(dists, indices):
                if dist <= threshold_km:
                    risk = classify_risk(dist)
                    if risk is not None:
                        d_row = debris_rows[idx]

                        vx1, vy1, vz1 = eu_row["vx_km_s"], eu_row["vy_km_s"], eu_row["vz_km_s"]
                        vx2, vy2, vz2 = d_row["vx_km_s"], d_row["vy_km_s"], d_row["vz_km_s"]
                        rel_vel = np.linalg.norm([vx1 - vx2, vy1 - vy2, vz1 - vz2])

                        all_events.append({
                            "timestamp": pd.Timestamp(t),
                            "satellite_1": eu_name,
                            "satellite_2": debris_names[idx],
                            "x1_km": eu_row["x_km"], "y1_km": eu_row["y_km"], "z1_km": eu_row["z_km"],
                            "vx1_km_s": vx1, "vy1_km_s": vy1, "vz1_km_s": vz1,
                            "x2_km": d_row["x_km"], "y2_km": d_row["y_km"], "z2_km": d_row["z_km"],
                            "vx2_km_s": vx2, "vy2_km_s": vy2, "vz2_km_s": vz2,
                            "miss_distance_km": round(dist, 6),
                            "relative_velocity_kms": round(rel_vel, 6),
                            "risk_class": risk
                        })

    if not all_events:
        logging.warning("⚠️ No conjunctions detected.")
        return pd.DataFrame()

    df = pd.DataFrame(all_events)
    df.sort_values(["satellite_1", "satellite_2", "timestamp"], inplace=True)
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eu-source", required=True, help="Path to EU satellite CSVs")
    parser.add_argument("--debris-source", required=True, help="Path to debris satellite CSVs")
    parser.add_argument("--output", required=True, help="Path to output directory (not a file)")
    parser.add_argument("--max-eu", type=int, default=10)
    parser.add_argument("--max-debris", type=int, default=100)
    parser.add_argument("--threshold-km", type=float, default=200)
    args = parser.parse_args()

    logging.info("📦 Loading satellite data from CSVs...")
    eu_data = load_satellite_data(args.eu_source)
    debris_data = load_satellite_data(args.debris_source)

    eu_data = dict(list(eu_data.items())[:args.max_eu])
    debris_data = dict(list(debris_data.items())[:args.max_debris])

    logging.info(f"🔍 Running conjunction detection for {len(eu_data)} EU and {len(debris_data)} debris satellites...")
    start = time.time()
    df = detect_conjunctions(eu_data, debris_data, threshold_km=args.threshold_km)
    logging.info(f"✅ Detection done in {time.time() - start:.2f}s")

    if df.empty:
        logging.warning("No conjunctions found. Exiting.")
        return

    os.makedirs(args.output, exist_ok=True)

    for risk in ["HIGH", "MODERATE", "LOW", "NEGLIGIBLE"]:
        df_risk = df[df["risk_class"] == risk]
        if not df_risk.empty:
            out_path = os.path.join(args.output, f"{risk.lower()}_risk_intervals.csv")
            df_risk.to_csv(out_path, index=False)
            logging.info(f"✅ Saved {len(df_risk)} {risk} risk events to {out_path}")


if __name__ == "__main__":
    main()
