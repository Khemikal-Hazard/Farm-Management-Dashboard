# main.py

import streamlit as st
import pandas as pd
from data import fetch_master_data, enrich_df_with_realtime_weather
from alerts import detect_risks_alert, detect_risks_map, generate_alert_export
from weather import render_weather_overlay
from map import render_farm_map

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="Farm Dashboard", layout="wide")
st.title("🌍 Farm Management Dashboard")
st.markdown("Visualizing farm plots with **profitability and real-time weather** using GIS points/polygons.")

# -------------------------------
# Load and Enrich Data
# -------------------------------
df = fetch_master_data()
df = enrich_df_with_realtime_weather(df)

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.markdown("### 🔎 Filters")
owners = st.sidebar.multiselect("Owner", options=df["owner"].dropna().unique())
seasons = st.sidebar.multiselect("Season", options=df["season"].dropna().unique())
locations = st.sidebar.multiselect("Farm Location", options=df["farm_location"].dropna().unique())

if owners:
    df = df[df["owner"].isin(owners)]
if seasons:
    df = df[df["season"].isin(seasons)]
if locations:
    df = df[df["farm_location"].isin(locations)]

# -------------------------------
# Sidebar Risk Controls
# -------------------------------
st.sidebar.markdown("### ⚠️ Risk Controls")
color_metric = st.sidebar.radio(
    "Color plots by:",
    options=["Profit Margin", "Temperature", "Rainfall", "Humidity"],
    index=0
)
show_only_alerts = st.sidebar.checkbox("Show only plots with alerts", value=False)

# -------------------------------
# Sidebar Weather Overlay
# -------------------------------
st.sidebar.markdown("### 📅 Weather Overlay")
selected_plots = st.sidebar.multiselect(
    "Select Plots for Weather Comparison",
    options=df["plot_id"].unique(),
    default=[df["plot_id"].iloc[0]]
)

# -------------------------------
# Risk Detection
# -------------------------------
risk_alerts = detect_risks_alert(df)
plot_alerts = detect_risks_map(df)

if show_only_alerts:
    df = df[df["plot_id"].isin(plot_alerts.keys())]

# -------------------------------
# Tabbed Layout
# -------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", "📈 Charts", "🚨 Alerts", "🌦️ Weather", "🗺️ Map", "📋 Data"
])

# -------------------------------
# Tab 1: Overview
# -------------------------------
with tab1:
    st.markdown("### 📊 Key Performance Indicators")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi4, kpi5, kpi6 = st.columns(3)

    with kpi1:
        st.metric("Total Cultivated Area (ha)", round(df["size_ha"].sum(), 2))
    with kpi2:
        st.metric("Crop Diversity", f"{len(df['crop_name'].dropna().unique())} crops")
    with kpi3:
        st.metric("Total Yield (tons)", round(df["actual_yield"].sum(), 2))
    with kpi4:
        st.metric("Profit Margin (%)", f"{round(df['profit_margin'].mean(), 2)}%")
    with kpi5:
        st.metric("Total Revenue (₵)", f"{df['total_revenue'].sum():,.2f}")
    with kpi6:
        st.metric("Total Expense (₵)", f"{df['total_expense'].sum():,.2f}")

    st.markdown("---")
    st.markdown("### 🌦️ Real-time Weather Averages")
    w1, w2, w3 = st.columns(3)
    with w1:
        st.metric("Avg Temp (°C)", round(pd.to_numeric(df["rt_temperature"], errors="coerce").mean(), 1))
    with w2:
        st.metric("Avg Humidity (%)", round(pd.to_numeric(df["rt_humidity"], errors="coerce").mean(), 1))
    with w3:
        st.metric("Avg Rainfall (mm)", round(pd.to_numeric(df["rt_rainfall"], errors="coerce").mean(), 2))

# -------------------------------
# Tab 2: Charts
# -------------------------------
with tab2:
    st.markdown("### 📈 Performance Charts")

    st.markdown("#### 📊 Yield by Owner")
    st.bar_chart(df.groupby("owner")["actual_yield"].sum())

    st.markdown("#### 💰 Input Costs per Owner")
    st.bar_chart(df.groupby("owner")["total_input_cost"].sum())

    st.markdown("#### ⚖️ Revenue vs Expense by Crop")
    rev_exp = df.groupby("crop_name")[["total_revenue", "total_expense"]].sum()
    st.bar_chart(rev_exp)

    st.markdown("#### 📉 Profit Margin by Owner")
    fig_profit = px.bar(df, x="owner", y="profit_margin", title="Profit Margin by Owner")
    st.plotly_chart(fig_profit, use_container_width=True)

    st.markdown("#### 🧪 Crop vs Revenue (Bubble by Yield)")
    fig_roi = px.scatter(
        df,
        x="crop_name",
        y="total_revenue",
        size="actual_yield",
        color="owner",
        title="Crop vs Revenue (Bubble by Yield)"
    )
    st.plotly_chart(fig_roi, use_container_width=True)

# -------------------------------
# Tab 3: Alerts
# -------------------------------
with tab3:
    st.markdown("### 🚨 Risk Alerts")

    if risk_alerts:
        for alert in risk_alerts:
            st.error(f"Plot {alert['plot_id']} ({alert['owner']}, {alert['location']}): " +
                     ", ".join(alert["issues"]))
    else:
        st.success("No critical alerts detected across filtered plots.")

    st.markdown("---")
    st.markdown("### 📥 Export Alert List")

    if risk_alerts:
        alert_df = generate_alert_export(df, plot_alerts)
        with st.expander("📋 View Alert Table"):
            st.dataframe(alert_df)

        st.download_button(
            label="Download Alert List as CSV",
            data=alert_df.to_csv(index=False),
            file_name=f"farm_alerts_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.markdown("### 📊 Alert Type Frequency")

    from collections import Counter
    all_issues = [issue for issues in plot_alerts.values() for issue in issues]
    issue_counts = Counter(all_issues)

    if issue_counts:
        alert_summary_df = pd.DataFrame({
            "Alert Type": list(issue_counts.keys()),
            "Count": list(issue_counts.values())
        })

        fig_alerts = px.bar(
            alert_summary_df,
            x="Alert Type",
            y="Count",
            color="Alert Type",
            title="Number of Plots Triggering Each Alert Type",
            text="Count"
        )
        st.plotly_chart(fig_alerts, use_container_width=True)
    else:
        st.info("No alert types to summarize.")

# -------------------------------
# Tab 4: Weather
# -------------------------------
with tab4:
    st.markdown("### 🌦️ Historical Weather Overlay")
    fig = render_weather_overlay(df, selected_plots)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No weather data available for selected plots.")

# -------------------------------
# Tab 5: Map
# -------------------------------
with tab5:
    st.markdown("### 🗺️ Farm Plots Map")
    farm_map = render_farm_map(df, plot_alerts, color_metric)
    st_folium(farm_map, width=900, height=600)

# -------------------------------
# Tab 6: Data Table
# -------------------------------
with tab6:
    st.markdown("### 📋 Farm Plot Data")
    with st.expander("🔍 View Filtered Farm Data"):
        st.dataframe(df)

    st.download_button(
        label="Download Filtered Data as CSV",
        data=df.to_csv(index=False),
        file_name="filtered_farm_data.csv",
        mime="text/csv"
    )