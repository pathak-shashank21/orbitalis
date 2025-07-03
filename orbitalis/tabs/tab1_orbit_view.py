
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from PIL import Image
import os
from datetime import datetime
from config import TEXTURE_PATH, PROPAGATED_EU_DIR
from utils.propagator_utils import safe_filename
from config import PROPAGATED_CONJUNCTION_DIR


def render(df, selected_risks, selected_satellite):
    st.subheader("3D Orbit Conjunction View")

    with st.sidebar:
        st.markdown("### 🛠 Orbit View Controls")
        show_orbit = st.checkbox("Show Orbit Trail", value=True)
        show_grid = st.checkbox("Show Lat/Lon Grid", value=True)
        spin_texture = st.checkbox("Simulate Earth Spin on Refresh", value=True)

    if df.empty or not all(c in df.columns for c in ["x_km", "y_km", "z_km"]):
        st.warning("Missing required 3D coordinate columns.")
        return

    fig = go.Figure()

    if not os.path.exists(TEXTURE_PATH):
        st.error(f"Earth texture not found at {TEXTURE_PATH}")
        return

    tex = np.array(Image.open(TEXTURE_PATH).transpose(Image.FLIP_TOP_BOTTOM).resize((360, 180))) / 255.0


    rotation_deg = (datetime.utcnow().timestamp() % 86400 / 86400) * 360 if spin_texture else 0
    lons = np.linspace(-np.pi, np.pi, tex.shape[1]) - np.radians(rotation_deg)
    lats = np.linspace(-np.pi/2, np.pi/2, tex.shape[0])
    lon2d, lat2d = np.meshgrid(lons, lats)

    r = 6371
    x = r * np.cos(lat2d) * np.cos(lon2d)
    y = r * np.cos(lat2d) * np.sin(lon2d)
    z = r * np.sin(lat2d)

    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        surfacecolor=np.mean(tex, axis=2),
        colorscale="gray",
        cmin=0, cmax=1,
        showscale=False,
        opacity=1.0,
        name="Earth",
        hoverinfo="skip"
    ))

    if show_grid:
        for lat in np.linspace(-80, 80, 9):
            lat_rad = np.radians(lat)
            lons = np.linspace(-np.pi, np.pi, 200)
            xg = r * np.cos(lat_rad) * np.cos(lons)
            yg = r * np.cos(lat_rad) * np.sin(lons)
            zg = r * np.full_like(lons, np.sin(lat_rad) * r)
            fig.add_trace(go.Scatter3d(
                x=xg, y=yg, z=zg, mode="lines",
                line=dict(color="gray", width=0.5),
                hoverinfo="skip", showlegend=False
            ))

        for lon in np.linspace(-180, 180, 13):
            lon_rad = np.radians(lon)
            lats = np.linspace(-np.pi/2, np.pi/2, 200)
            xg = r * np.cos(lats) * np.cos(lon_rad)
            yg = r * np.cos(lats) * np.sin(lon_rad)
            zg = r * np.sin(lats)
            fig.add_trace(go.Scatter3d(
                x=xg, y=yg, z=zg, mode="lines",
                line=dict(color="gray", width=0.5),
                hoverinfo="skip", showlegend=False
            ))

        RISK_COLORS = {"High": "red", "Moderate": "orange", "Low": "yellow", "Negligible": "lightblue"}

    for risk in selected_risks:
        subset = df[df["risk_level"].str.upper() == risk.upper()]
        if subset.empty:
            continue

        # Support both 'timestamp' and 'start_timestamp' field names
        time_col = "start_timestamp" if "start_timestamp" in subset.columns else "timestamp"
        miss_col = "miss_distance_km" if "miss_distance_km" in subset.columns else "min_distance_km"

        hover_text = [
            f"<b>{row['satellite_1']}</b> ↔ <b>{row['satellite_2']}</b><br>"
            f"Min Dist: {row.get(miss_col, 0):.2f} km<br>"
            f"Rel Vel: {row.get('relative_velocity_kms', 0):.2f} km/s<br>"
            f"Timestamp: {row[time_col]}"
            for _, row in subset.iterrows()
        ]

        fig.add_trace(go.Scatter3d(
            x=subset["x1_km"],  # Use satellite_1 position as point location
            y=subset["y1_km"],
            z=subset["z1_km"],
            mode="markers",
            marker=dict(color=RISK_COLORS.get(risk, "gray"), size=6, opacity=0.95),
            name=risk,
            text=hover_text,
            hoverinfo="text"
        ))


    if show_orbit and selected_satellite:
        orbit_file = os.path.join(PROPAGATED_CONJUNCTION_DIR, f"{safe_filename(selected_satellite)}.csv")

        if os.path.exists(orbit_file):
            orbit_df = pd.read_csv(orbit_file, parse_dates=["timestamp"])
            orbit_df.dropna(subset=["x_km", "y_km", "z_km"], inplace=True)
            segments = 20
            seg_len = len(orbit_df) // segments
            for i in range(segments):
                start, end = i * seg_len, (i + 1) * seg_len
                fig.add_trace(go.Scatter3d(
                    x=orbit_df["x_km"].iloc[start:end],
                    y=orbit_df["y_km"].iloc[start:end],
                    z=orbit_df["z_km"].iloc[start:end],
                    mode="lines",
                    line=dict(color=f"rgba(0,255,255,{(i + 1) / segments:.2f})", width=0.7),
                    hoverinfo="skip",
                    showlegend=False
                ))
        else:
            st.info(f"Orbit file not found: {safe_filename(selected_satellite)}.csv")

    zoom_range = 8000
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, range=[-zoom_range, zoom_range]),
            yaxis=dict(visible=False, range=[-zoom_range, zoom_range]),
            zaxis=dict(visible=False, range=[-zoom_range, zoom_range]),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=1),
            bgcolor="black"
        ),
        paper_bgcolor="black",
        plot_bgcolor="black",
        margin=dict(l=0, r=0, b=0, t=40),
        legend=dict(bgcolor='rgba(0,0,0,0)', font_color='white'),
        title="3D Earth + Conjunctions + Orbit Trails"
    )

    st.plotly_chart(fig, use_container_width=True)
