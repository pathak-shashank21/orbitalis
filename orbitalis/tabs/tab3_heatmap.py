import streamlit as st
import plotly.express as px
import pandas as pd

def render(df):
    st.subheader("Conjunction Risk Counts Over Time")

    if df.empty or "start_timestamp" not in df.columns:
        st.info("No heatmap data available.")
        return

    # Ensure timestamps are datetime
    if not pd.api.types.is_datetime64_any_dtype(df["start_timestamp"]):
        df["start_timestamp"] = pd.to_datetime(df["start_timestamp"], errors="coerce")

    # Extract calendar day
    df["timestamp_day"] = df["start_timestamp"].dt.date

    # Count conjunctions per day and risk level
    heat_df = (
        df.groupby(["timestamp_day", "risk_level"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    if heat_df.empty:
        st.warning("No risk-level data available to plot.")
        return

    # Optional: Show raw daily counts
    with st.expander("View Daily Risk Count Table"):
        st.dataframe(heat_df)

    # Area chart of conjunction trends
    heat_fig = px.area(
        heat_df,
        labels={"value": "Count", "timestamp_day": "Date"},
        title="Daily Conjunction Risk Levels Over Time"
    )

    heat_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Conjunctions",
        plot_bgcolor="black",
        paper_bgcolor="black",
        font=dict(color="white"),
        legend_title="Risk Level"
    )

    st.plotly_chart(heat_fig, use_container_width=True)
