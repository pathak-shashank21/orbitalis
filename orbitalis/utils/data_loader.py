import pandas as pd
from config import RISK_LEVELS

def load_data():
    all_rows = []
    for level, path in RISK_LEVELS.items():
        try:
            df = pd.read_csv(path, parse_dates=["timestamp"])

            # Add risk level as a column
            df["risk_level"] = level

            # Ensure essential position columns exist
            required_cols = ["x1_km", "y1_km", "z1_km", "miss_distance_km"]
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Standardize column names for plotting
            df["x_km"] = df["x1_km"]
            df["y_km"] = df["y1_km"]
            df["z_km"] = df["z1_km"]
            df["min_distance_km"] = df["miss_distance_km"]

            # Handle optional velocity column fallback
            if "relative_velocity_kms" not in df.columns:
                df["relative_velocity_kms"] = 0.0  # Default if missing

            # Add windowed timestamp range
            df["start_timestamp"] = df["timestamp"]
            df["end_timestamp"] = df["timestamp"] + pd.Timedelta(seconds=60)

            all_rows.append(df)

        except Exception as e:
            print(f"⚠️ Could not load {path}: {e}")

    if not all_rows:
        return pd.DataFrame()

    return pd.concat(all_rows, ignore_index=True)
