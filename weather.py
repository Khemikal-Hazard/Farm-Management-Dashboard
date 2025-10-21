# weather.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data import fetch_weather_history

# -------------------------------
# Render Historical Weather Overlay
# -------------------------------
def render_weather_overlay(df: pd.DataFrame, selected_plots: list):
    weather_frames = []
    for pid in selected_plots:
        row = df[df["plot_id"] == pid].iloc[0]
        wdf = fetch_weather_history(pid, row["planting_date"], row["actual_harvest_date"])
        if not wdf.empty:
            wdf["Plot ID"] = pid
            wdf["Owner"] = row["owner"]
            wdf["Crop"] = row["crop_name"]
            wdf["Yield (tons)"] = row["actual_yield"]
            wdf["Profit Margin (%)"] = row["profit_margin"]
            weather_frames.append(wdf)

    combined_weather = pd.concat(weather_frames) if weather_frames else pd.DataFrame()

    if combined_weather.empty:
        return None

    fig = px.line(
        combined_weather,
        x="record_date",
        y="temperature_c",
        color="Plot ID",
        line_dash="Owner",
        title="Temperature Trends by Plot"
    )

    fig.add_bar(
        x=combined_weather["record_date"],
        y=combined_weather["rainfall_mm"],
        name="Rainfall (mm)",
        opacity=0.4
    )

    fig.update_layout(
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(title="Yield / Profit", overlaying="y", side="right"),
        legend_title="Plot ID"
    )

    for pid in selected_plots:
        subset = combined_weather[combined_weather["Plot ID"] == pid]
        if not subset.empty:
            fig.add_scatter(
                x=[subset["record_date"].min()],
                y=[subset["Yield (tons)"].iloc[0]],
                mode="markers+text",
                name=f"Yield ({pid})",
                yaxis="y2",
                marker=dict(symbol="circle", size=10)
            )
            fig.add_scatter(
                x=[subset["record_date"].max()],
                y=[subset["Profit Margin (%)"].iloc[0]],
                mode="markers+text",
                name=f"Profit Margin ({pid})",
                yaxis="y2",
                marker=dict(symbol="diamond", size=10)
            )

    return fig