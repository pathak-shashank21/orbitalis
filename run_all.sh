#!/bin/bash

set -e
echo "🌍 Starting orbitalis pipeline..."

# === 1. Setup virtual environment ===
ENV_DIR=".venv_orbitalis"

if [ ! -d "$ENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$ENV_DIR"
fi

echo "🐍 Activating virtual environment..."
source "$ENV_DIR/bin/activate"

echo "⬇️ Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

# === 2. Propagate EU sats ===
echo "📡 Propagating EU satellites..."
python3 orbitalis/demo/propagator.py \
    --tle orbitalis/demo/input_tle/eu_active.tle \
    --output output/propagated_eu_sats \
    --duration 1440 \
    --step 60

# === 3. Propagate space debris ===
echo "🪨 Propagating space debris..."
python3 orbitalis/demo/propagator.py \
    --tle orbitalis/demo/input_tle/space_debris.tle \
    --output output/propagated_debris \
    --duration 1440 \
    --step 60

# === 4. Conjunction detection ===
echo "🛰️ Detecting conjunctions..."
python3 orbitalis/demo/conjunction_combined_xyz_vxyz.py \
    --eu-source output/propagated_eu_sats \
    --debris-source output/propagated_debris \
    --output output/conjunction_events \
    --threshold-km 3000 \


# === 5. Launch Streamlit dashboard ===
echo "🚀 Launching dashboard..."
streamlit run orbitalis/app.py
