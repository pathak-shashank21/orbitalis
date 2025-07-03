import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import glob
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Try to import Earth texture mesh
try:
    from visualization.earth_texture import textured_earth_mesh
except ImportError:
    def textured_earth_mesh(fig):
        pass  # fallback to blank Earth sphere if texture module not available

def plot_3d_orbits(selected_files):
    fig = go.Figure()

    for path in selected_files:
        fname = os.path.basename(path)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            st.warning(f"Failed to read {fname}: {e}")
            continue

        if df.empty or not all(k in df.columns for k in ['x_km', 'y_km', 'z_km']):
            st.warning(f"File {fname} is invalid or missing columns.")
            continue

        name = df['name'].iloc[0] if 'name' in df.columns else fname.replace(".csv", "")
        is_debris = "propagated_debris" in path or "DEBRIS" in name.upper()
        color = "red" if is_debris else "cyan"

        fig.add_trace(go.Scatter3d(
            x=df['x_km'], y=df['y_km'], z=df['z_km'],
            mode='lines',
            line=dict(width=1, color=color),
            name=name,
            hoverinfo='text',
            text=[f"{name}<br>x={x:.1f}, y={y:.1f}, z={z:.1f} km"
                  for x, y, z in zip(df['x_km'], df['y_km'], df['z_km'])]
        ))

        # Final position marker
        final_x, final_y, final_z = df['x_km'].iloc[-1], df['y_km'].iloc[-1], df['z_km'].iloc[-1]
        fig.add_trace(go.Scatter3d(
            x=[final_x], y=[final_y], z=[final_z],
            mode='markers',
            marker=dict(size=4, color=color, opacity=1.0),
            name=f"{name} (now)",
            hoverinfo='text',
            text=[f"{name} Current Position<br>x={final_x:.1f}<br>y={final_y:.1f}<br>z={final_z:.1f} km"]
        ))

    # ✅ ADD EARTH after adding orbits
    textured_earth_mesh(fig)

    # Final layout
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            aspectmode='data',
            xaxis=dict(title='x', showgrid=True),
            yaxis=dict(title='y', showgrid=True),
            zaxis=dict(title='z', showgrid=True),
        ),
        showlegend=True,
    )

    return fig


def render():
    st.subheader("Earth + Realistic Conjunction Trails")

    # Limit to 100 of each
    sat_files = sorted(glob.glob("output/propagated_eu_sats/*.csv"))[:100]
    debris_files = sorted(glob.glob("output/propagated_debris/*.csv"))[:100]
    files = sat_files + debris_files

    if not files:
        st.warning("No satellite or debris data found.")
        return

    total = len(files)
    preview = ", ".join(os.path.basename(f) for f in files[:5])

    fig = plot_3d_orbits(files)
    st.plotly_chart(fig, use_container_width=True)
