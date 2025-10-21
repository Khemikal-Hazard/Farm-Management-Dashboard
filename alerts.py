# alerts.py

import pandas as pd
from datetime import datetime

# -------------------------------
# Detect Risk Alerts (List Format)
# -------------------------------
def detect_risks_alert(df: pd.DataFrame):
    alerts = []
    for _, row in df.iterrows():
        issues = []
        if pd.to_numeric(row.get("profit_margin", 0), errors="coerce") < 0:
            issues.append("Negative profit")
        if pd.to_numeric(row.get("yield_gap", 0), errors="coerce") > 10:
            issues.append("High yield gap")
        if pd.to_numeric(row.get("rt_rainfall", 0), errors="coerce") > 50:
            issues.append("Heavy rainfall")
        if issues:
            alerts.append({
                "plot_id": row["plot_id"],
                "owner": row["owner"],
                "location": row["farm_location"],
                "issues": issues
            })
    return alerts

# -------------------------------
# Detect Risk Alerts (Map Format)
# -------------------------------
def detect_risks_map(df: pd.DataFrame):
    alert_map = {}
    for _, row in df.iterrows():
        issues = []
        if pd.to_numeric(row.get("profit_margin", 0), errors="coerce") < 0:
            issues.append("Negative profit")
        if pd.to_numeric(row.get("yield_gap", 0), errors="coerce") > 10:
            issues.append("High yield gap")
        if pd.to_numeric(row.get("rt_rainfall", 0), errors="coerce") > 50:
            issues.append("Heavy rainfall")
        if issues:
            alert_map[row["plot_id"]] = issues
    return alert_map

# -------------------------------
# Export Alert List to CSV
# -------------------------------
def generate_alert_export(df: pd.DataFrame, plot_alerts: dict):
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_df = pd.DataFrame([
        {
            "Plot ID": row["plot_id"],
            "Owner": row["owner"],
            "Location": row["farm_location"],
            "Cycle ID": row["cycle_id"],
            "Crop": row["crop_name"],
            "Profit Margin (%)": row["profit_margin"],
            "Alert Issues": ", ".join(issues),
            "Exported At": export_time
        }
        for _, row in df.iterrows()
        if row["plot_id"] in plot_alerts
        for issues in [plot_alerts[row["plot_id"]]]
    ])
    return alert_df