import streamlit as st
from config import RISK_LEVELS
from utils.data_loader import load_data
from utils.propagator_utils import safe_filename

import tabs.tab1_orbit_view as tab1
import tabs.tab2_timeline as tab2
import tabs.tab3_heatmap as tab3
import tabs.tab4_earth_trails as tab4

import os
import glob

st.set_page_config(layout="wide", page_title="SSA Risk Dashboard")

# Load conjunction data
df_all = load_data()

st.title("Space Situational Awareness (SSA) Dashboard")
st.markdown("Monitor conjunction risks between EU satellites and debris.")

if df_all.empty:
    st.error("No conjunction data found.")
    st.stop()

# --- Sidebar filters only affect tab1-tab3 ---
with st.sidebar:
    st.header("🔍 Filter")
    eu_sats = sorted(df_all["satellite_1"].unique())
    selected_sats = st.multiselect("Select EU Satellite(s)", eu_sats, default=eu_sats[:1])

    selected_risks = st.multiselect(
        "Risk Level",
        list(RISK_LEVELS.keys()),
        default=list(RISK_LEVELS.keys())
    )

    filtered_df = df_all[
        (df_all["satellite_1"].isin(selected_sats)) &
        (df_all["risk_level"].str.upper().isin([r.upper() for r in selected_risks]))
    ]

    st.header("⬇️ Export")
    if not filtered_df.empty:
        st.download_button(
            label="Download filtered CSV",
            data=filtered_df.to_csv(index=False),
            file_name=f"conjunctions_filtered.csv",
            mime="text/csv"
        )

    st.header("🪐 Orbit View Controls")
    st.checkbox("Show Orbit Trail", value=True, key="show_orbit")
    st.checkbox("Show Lat/Lon Grid", value=True, key="show_grid")
    st.checkbox("Simulate Earth Spin on Refresh", value=True, key="simulate_spin")

# --- For tab 4: Load all satellite + debris files automatically ---
sat_folder = "output/propagated_eu_sats"
debris_folder = "output/propagated_debris"

sat_files = sorted(glob.glob(f"{sat_folder}/*.csv"))
debris_files = sorted(glob.glob(f"{debris_folder}/*.csv"))

# Combine for visualization in tab4
all_files = sat_files + debris_files
st.session_state["filtered_files"] = all_files

# --- Tabs ---
tab1_, tab2_, tab3_, tab4_ = st.tabs([
    "Orbit View", "Timeline", "Risk Heatmap", "Earth + Trails"
])

with tab1_:
    tab1.render(filtered_df, selected_risks, selected_sats[0] if selected_sats else "")

with tab2_:
    tab2.render(filtered_df)

with tab3_:
    tab3.render(filtered_df)

with tab4_:
    tab4.render()
