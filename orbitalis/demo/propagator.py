import os
import csv
import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from sgp4.api import Satrec, WGS72, jday

# --- Logging ---
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.INFO)

def jd_to_datetime(jd: float) -> datetime:
    return datetime.utcfromtimestamp((jd - 2440587.5) * 86400.0)

def load_tles(tle_path: str, start_time: datetime, max_age_hours=72) -> List[Tuple[str, Satrec]]:
    sats = []
    with open(tle_path, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
        i = 0
        while i < len(lines):
            if i + 2 < len(lines) and lines[i+1].startswith("1 ") and lines[i+2].startswith("2 "):
                name = lines[i].strip()
                line1 = lines[i+1]
                line2 = lines[i+2]
                try:
                    sat = Satrec.twoline2rv(line1, line2)
                    sats.append((name, sat))
                except Exception as e:
                    logging.error(f"Failed to parse TLE: {name} → {e}")
                i += 3
            elif i + 1 < len(lines) and lines[i].startswith("1 ") and lines[i+1].startswith("2 "):
                line1 = lines[i]
                line2 = lines[i+1]
                try:
                    name = line1.split()[1]
                    sat = Satrec.twoline2rv(line1, line2)
                    sats.append((name, sat))
                except Exception as e:
                    logging.error(f"Failed to parse fallback TLE at line {i}: {e}")
                i += 2
            else:
                i += 1
    logging.info(f"✅ Loaded {len(sats)} satellites from {tle_path}")
    return sats

def propagate_single(sat: Satrec, start_time: datetime, duration_min: int, step_sec: int):
    num_steps = int(duration_min * 60 / step_sec)
    timestamps, positions, velocities = [], [], []

    logging.debug(f"  ↪️  Steps: {num_steps} | Δt = {step_sec}s")
    for step in range(num_steps):
        dt = start_time + timedelta(seconds=step * step_sec)
        jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond * 1e-6)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            timestamps.append(dt)
            positions.append(r)
            velocities.append(v)
        else:
            logging.warning(f"SGP4 error {e} at {dt}")
            timestamps.append(dt)
            positions.append([np.nan]*3)
            velocities.append([np.nan]*3)

    return np.array(timestamps), np.array(positions), np.array(velocities)

def propagate_monte_carlo(sat, start_time, duration_min, step_sec, mc_runs, sigma_pos_km, sigma_vel_kms):
    timestamps, base_positions, base_velocities = propagate_single(sat, start_time, duration_min, step_sec)
    results_r, results_v = [], []

    for _ in range(mc_runs):
        perturbed_r = base_positions + np.random.normal(0, sigma_pos_km, base_positions.shape)
        perturbed_v = base_velocities + np.random.normal(0, sigma_vel_kms, base_velocities.shape)
        results_r.append(perturbed_r)
        results_v.append(perturbed_v)

    positions = np.stack(results_r)
    velocities = np.stack(results_v)

    pos_mean = np.nanmean(positions, axis=0)
    pos_std = np.nanstd(positions, axis=0)
    vel_mean = np.nanmean(velocities, axis=0)

    return timestamps, pos_mean, pos_std, vel_mean



def safe_filename(name: str) -> str:
    return (
        name.replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("-", "_")
            .replace("/", "_")
    )

def save_standard_csv(timestamps, positions, velocities, out_path: str, name: str):
    os.makedirs(out_path, exist_ok=True)
    file = os.path.join(out_path, f"{safe_filename(name)}.csv")
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s", "name"])
        for i in range(len(timestamps)):
            row = [timestamps[i].isoformat()] + positions[i].tolist() + velocities[i].tolist() + [name]
            writer.writerow(row)
    logging.info(f"✅ Saved: {file}")

def save_csv_with_uncertainty(timestamps, mean_r, std_r, mean_v, out_path: str, name: str):
    os.makedirs(out_path, exist_ok=True)
    file = os.path.join(out_path, f"{safe_filename(name)}_mc.csv")
    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "x_km", "y_km", "z_km",
            "vx_km_s", "vy_km_s", "vz_km_s",
            "sx_km", "sy_km", "sz_km", "name"
        ])
        for i in range(len(timestamps)):
            row = (
                [timestamps[i].isoformat()] +
                mean_r[i].tolist() +
                mean_v[i].tolist() +
                std_r[i].tolist() +
                [name]
            )
            writer.writerow(row)
    logging.info(f"✅ MC Saved: {file}")


def propagate_all(tle_path, out_dir, duration_min, step_sec, limit, filter_key, mc_runs, sigma_pos, sigma_vel):
    logging.info(f"🚀 Propagating from TLE: {tle_path}")
    logging.info(f"⏱ Duration: {duration_min} min | Step: {step_sec} sec | Max: {limit or 'ALL'} sats")

    sats = load_tles(tle_path, start_time=None)  # `start_time` no longer needed here

    if filter_key:
        sats = [s for s in sats if filter_key.lower() in s[0].lower()]
    if limit:
        sats = sats[:limit]

    for idx, (name, sat) in enumerate(sats):
        logging.info(f"🛰️ [{idx+1}/{len(sats)}] {name}")
        try:
            # Compute satellite-specific epoch-based start time
            start_time = jd_to_datetime(sat.jdsatepoch + sat.jdsatepochF)

            if mc_runs:
                t, mean_r, std_r, mean_v = propagate_monte_carlo(
                    sat, start_time, duration_min, step_sec,
                    mc_runs, sigma_pos, sigma_vel
                )
                save_csv_with_uncertainty(t, mean_r, std_r, mean_v, out_dir, name)

            else:
                t, r, v = propagate_single(sat, start_time, duration_min, step_sec)
                save_standard_csv(t, r, v, out_dir, name)
        except Exception as e:
            logging.error(f"[{name}] ❌ Failed: {e}")

    logging.info("🎯 All satellites processed.")


def main():
    parser = argparse.ArgumentParser(description="SGP4 TLE Propagation + Monte Carlo")
    parser.add_argument("--tle", required=True, help="TLE input file")
    parser.add_argument("--output", default="output/propagated", help="Directory to save results")
    parser.add_argument("--duration", type=int, default=1440, help="Propagation time in minutes")
    parser.add_argument("--step", type=int, default=60, help="Time step in seconds")
    parser.add_argument("--limit", type=int, help="Max number of satellites to run")
    parser.add_argument("--filter", help="Filter satellite names")
    parser.add_argument("--monte-carlo", type=int, help="Number of MC simulations")
    parser.add_argument("--sigma-pos", type=float, default=0.1, help="Position perturbation (km)")
    parser.add_argument("--sigma-vel", type=float, default=0.0001, help="Velocity perturbation (km/s)")
    args = parser.parse_args()

    t0 = time.time()
    propagate_all(
        tle_path=args.tle,
        out_dir=args.output,
        duration_min=args.duration,
        step_sec=args.step,
        limit=args.limit,
        filter_key=args.filter,
        mc_runs=args.monte_carlo,
        sigma_pos=args.sigma_pos,
        sigma_vel=args.sigma_vel
    )
    logging.info(f"⏳ Total time: {time.time() - t0:.2f} seconds")


if __name__ == "__main__":
    main()
