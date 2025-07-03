import streamlit as st
import plotly.express as px
import pandas as pd

def render(df):
    st.subheader("Conjunction Duration Timeline")

    if df.empty:
        st.info("No timeline data available.")
        return

    # Label for Y-axis
    df["label"] = df["satellite_1"] + " ↔ " + df["satellite_2"]

    # Ensure start and end timestamps exist
    df["start_timestamp"] = pd.to_datetime(df.get("start_timestamp", df["timestamp"]))
    df["end_timestamp"] = pd.to_datetime(df.get("end_timestamp", df["timestamp"]))

    # Duration in minutes
    df["duration_min"] = (df["end_timestamp"] - df["start_timestamp"]).dt.total_seconds() / 60

    # Construct hover info
    df["hover_text"] = df.apply(lambda row: (
        f"🛰️ {row['satellite_1']} ↔ {row['satellite_2']}<br>"
        f"📏 Miss Dist: {row.get('miss_distance_km', row.get('min_distance_km', 0)):.2f} km<br>"
        f"⚡ Rel Vel: {row.get('relative_velocity_kms', 0):.2f} km/s<br>"
        f"Start: {row['start_timestamp']}<br>"
        f"End: {row['end_timestamp']}"
    ), axis=1)

    # Sort for clarity
    df.sort_values(by=["risk_level", "duration_min"], ascending=[True, False], inplace=True)

    # Plotly timeline
    fig = px.timeline(
        df,
        x_start="start_timestamp",
        x_end="end_timestamp",
        y="label",
        color="risk_level",
        hover_name="hover_text"
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="Conjunction Risk Timeline by Satellite Pair",
        xaxis_title="Time (UTC)",
        yaxis_title="Conjunction",
        legend_title="Risk Level",
        hoverlabel=dict(bgcolor="black", font_size=12, font_family="monospace"),
        plot_bgcolor="black",
        paper_bgcolor="black",
        font=dict(color="white")
    )

    st.plotly_chart(fig, use_container_width=True)
