# map.py

import folium
import json
import pandas as pd
import branca.colormap as cm
from streamlit_folium import st_folium
from data import extract_lat_lon_from_wkt

# -------------------------------
# Render Farm Map
# -------------------------------
def render_farm_map(df: pd.DataFrame, plot_alerts: dict, metric: str):
    # Determine metric and color scale
    if metric == "Profit Margin":
        metric_col = "profit_margin"
        vmin, vmax = -50, 100
        colors = ["red", "yellow", "green"]
        caption = "Profit Margin (%)"
    elif metric == "Temperature":
        metric_col = "rt_temperature"
        series = pd.to_numeric(df[metric_col], errors="coerce").dropna()
        vmin, vmax = (series.min(), series.max()) if not series.empty else (0, 40)
        if vmin == vmax: vmin, vmax = vmin - 1, vmax + 1
        colors = ["blue", "lightblue", "orange", "red"]
        caption = "Temperature (°C)"
    elif metric == "Rainfall":
        metric_col = "rt_rainfall"
        series = pd.to_numeric(df[metric_col], errors="coerce").dropna()
        vmin, vmax = 0, float(series.max()) if not series.empty else 10
        if vmin == vmax: vmax = vmin + 1
        colors = ["white", "lightblue", "blue", "darkblue"]
        caption = "Rainfall (mm)"
    else:  # Humidity
        metric_col = "rt_humidity"
        series = pd.to_numeric(df[metric_col], errors="coerce").dropna()
        vmin, vmax = (series.min(), series.max()) if not series.empty else (0, 100)
        if vmin == vmax: vmin, vmax = vmin - 1, vmax + 1
        colors = ["#f7fbff", "#6baed6", "#08306b"]
        caption = "Humidity (%)"

    colormap = cm.LinearColormap(colors=colors, vmin=vmin, vmax=vmax, caption=caption)
    farm_map = folium.Map(location=[5.55, -0.2], zoom_start=7, tiles="CartoDB positron")

    for _, plot in df.iterrows():
        value = plot.get(metric_col)
        color = colormap(value if pd.notna(value) else vmin)
        plot_id = plot["plot_id"]
        alert_badge = ""
        if plot_id in plot_alerts:
            alert_badge = "<br><b style='color:red;'>⚠️ " + ", ".join(plot_alerts[plot_id]) + "</b>"

        popup_html = f"""
        <b>{plot.get('owner','')}</b><br>
        Area: {plot.get('size_ha', 'N/A')} ha<br>
        Crop: {plot.get('crop_name', 'N/A')}<br>
        Expected Yield: {plot.get('expected_yield', 0)} tons<br>
        Actual Yield: {plot.get('actual_yield', 0)} tons<br>
        Revenue: ₵{plot.get('total_revenue', 0):,}<br>
        Expense: ₵{plot.get('total_expense', 0):,}<br>
        Profit: ₵{plot.get('profit', 0):,}<br>
        Profit Margin: {plot.get('profit_margin','N/A')} %<br>
        🌡️ Temp: {plot.get('rt_temperature','N/A')} °C<br>
        💧 Humidity: {plot.get('rt_humidity','N/A')} %<br>
        🌧️ Rainfall: {plot.get('rt_rainfall','N/A')} mm
        {alert_badge}
        """

        try:
            geom = str(plot.get("location_geometry", ""))
            if geom.startswith("["):
                coords = json.loads(geom)
                folium.Polygon(
                    locations=coords,
                    color="red" if plot_id in plot_alerts else color,
                    weight=3 if plot_id in plot_alerts else 1,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.6,
                    popup=popup_html
                ).add_to(farm_map)
            else:
                lat, lon = extract_lat_lon_from_wkt(geom)
                if lat is not None and lon is not None:
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=6,
                        color="red" if plot_id in plot_alerts else color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.7,
                        popup=popup_html
                    ).add_to(farm_map)
        except Exception as e:
            print(f"Error rendering geometry for owner {plot.get('owner','')}: {e}")

    colormap.add_to(farm_map)
    return farm_map