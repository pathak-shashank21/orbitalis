import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
import os

def generate_orbit_trails_plot():
    # Load conjunctions with coordinates
    base = "demo/conjunction_coordinates"
    dfs = []
    for risk in ["high", "moderate", "low", "negligible"]:
        f = os.path.join(base, f"{risk}_risk_intervals_with_coords.csv")
        if os.path.exists(f):
            d = pd.read_csv(f, parse_dates=["start_timestamp"])
            d["risk"] = risk.upper()
            dfs.append(d)
    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    # Load Earth texture image
    texture_path = os.path.join("visualization", "earth_texture.jpg")
    tex = Image.open(texture_path).resize((360, 180))
    tex = np.array(tex) / 255.0

    lons = np.linspace(-np.pi, np.pi, tex.shape[1])
    lats = np.linspace(-np.pi / 2, np.pi / 2, tex.shape[0])
    lon2d, lat2d = np.meshgrid(lons, lats)
    r = 6371  # Earth radius in km
    xe = r * np.cos(lat2d) * np.cos(lon2d)
    ye = r * np.cos(lat2d) * np.sin(lon2d)
    ze = r * np.sin(lat2d)

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=xe, y=ye, z=ze,
        surfacecolor=tex[:, :, 0],
        colorscale='gray',
        cmin=0, cmax=1,
        showscale=False,
        opacity=0.9
    ))

    colors = {
        "HIGH": "red",
        "MODERATE": "orange",
        "LOW": "yellowgreen",
        "NEGLIGIBLE": "lightblue"
    }

    for risk, group in df.groupby("risk"):
        coords = group.sort_values("start_timestamp")[["x_km", "y_km", "z_km"]]
        fig.add_trace(go.Scatter3d(
            x=coords["x_km"], y=coords["y_km"], z=coords["z_km"],
            mode='lines+markers',
            marker=dict(size=2, color=colors[risk]),
            line=dict(width=1.5, color=colors[risk]),
            name=f"{risk} trail"
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X [km]", showbackground=False),
            yaxis=dict(title="Y [km]", showbackground=False),
            zaxis=dict(title="Z [km]", showbackground=False),
            aspectmode='data',
            bgcolor='black'
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        paper_bgcolor='black',
        legend=dict(bgcolor='rgba(0,0,0,0.5)', font_color='white'),
        title="🌍 Earth with Satellite Conjunction Trails"
    )

    return fig
