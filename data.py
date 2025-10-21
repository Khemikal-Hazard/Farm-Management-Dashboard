# data.py

import os
import pandas as pd
import mysql.connector
import requests
from dotenv import load_dotenv
from shapely import wkt

# Load environment variables
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Khemikal1234")
DB_NAME = os.getenv("DB_NAME", "farm_management_database")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# -------------------------------
# MySQL Connection
# -------------------------------
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -------------------------------
# Master Farm Data Query
# -------------------------------
def fetch_master_data():
    conn = get_connection()
    query = """ 
    SELECT 
        fp.plot_id, fp.farm_location, fp.owner, fp.size_ha,
        b.location_id, b.location_geometry,
        cc.cycle_id, cc.planting_date, cc.actual_harvest_date, c.crop_name, cc.season,
        yr.expected_yield, yr.actual_yield,
        (yr.actual_yield - yr.expected_yield) AS yield_gap,
        SUM(CASE WHEN ir.input_type = 'Vines' THEN ir.quantity_used ELSE 0 END) AS vines_used,
        SUM(CASE WHEN ir.input_type = 'Fertilizer' THEN ir.quantity_used ELSE 0 END) AS fertilizer_used,
        SUM(CASE WHEN ir.input_type = 'Pesticide' THEN ir.quantity_used ELSE 0 END) AS pesticide_used,
        SUM(CASE WHEN ir.input_type = 'Traction' THEN ir.quantity_used ELSE 0 END) AS traction_used,
        SUM(CASE WHEN ir.input_type = 'Irrigation' THEN ir.quantity_used ELSE 0 END) AS irrigation_used,
        SUM(CASE WHEN ir.input_type = 'Other' THEN ir.quantity_used ELSE 0 END) AS other_inputs_used,
        SUM(ir.cost) AS total_input_cost,
        SUM(CASE WHEN fr.transaction_type = 'Revenue' THEN fr.amount_10k ELSE 0 END) AS total_revenue,
        SUM(CASE WHEN fr.transaction_type = 'Expense' THEN fr.amount_10k ELSE 0 END) AS total_expense,
        (SUM(CASE WHEN fr.transaction_type = 'Revenue' THEN fr.amount_10k ELSE 0 END) -
         SUM(CASE WHEN fr.transaction_type = 'Expense' THEN fr.amount_10k ELSE 0 END)) AS profit,
        CASE 
            WHEN SUM(CASE WHEN fr.transaction_type = 'Revenue' THEN fr.amount_10k ELSE 0 END) > 0
            THEN ROUND((
                (SUM(CASE WHEN fr.transaction_type = 'Revenue' THEN fr.amount_10k ELSE 0 END) -
                 SUM(CASE WHEN fr.transaction_type = 'Expense' THEN fr.amount_10k ELSE 0 END))
                /
                SUM(CASE WHEN fr.transaction_type = 'Revenue' THEN fr.amount_10k ELSE 0 END)
            ) * 100, 2)
            ELSE NULL
        END AS profit_margin,
        AVG(wr.rainfall_mm) AS avg_rainfall,
        AVG(wr.temperature_c) AS avg_temperature,
        AVG(wr.humidity) AS avg_humidity
    FROM FarmPlot fp
    LEFT JOIN Bearings b ON fp.plot_id = b.plot_id
    LEFT JOIN CropCycle cc ON fp.plot_id = cc.plot_id
    LEFT JOIN Crop c ON cc.cycle_id = c.cycle_id
    LEFT JOIN YieldRecord yr ON cc.cycle_id = yr.cycle_id
    LEFT JOIN InputRecord ir ON cc.cycle_id = ir.cycle_id
    LEFT JOIN FinanceRecord fr ON cc.cycle_id = fr.cycle_id
    LEFT JOIN WeatherRecord wr ON fp.plot_id = wr.plot_id
       AND wr.record_date BETWEEN cc.planting_date AND cc.actual_harvest_date
    GROUP BY 
        fp.plot_id, fp.farm_location, fp.owner, fp.size_ha,
        b.location_id, b.location_geometry,
        cc.cycle_id, cc.season, cc.planting_date, cc.actual_harvest_date, c.crop_name,
        yr.expected_yield, yr.actual_yield;
    """ 
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -------------------------------
# Real-Time Weather Enrichment
# -------------------------------
def extract_lat_lon_from_wkt(geom_str: str):
    try:
        point = wkt.loads(geom_str)
        return point.y, point.x
    except Exception:
        return None, None

def fetch_realtime_weather(lat: float, lon: float):
    if not WEATHER_API_KEY:
        return {"temperature": None, "humidity": None, "rainfall": None}
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "temperature": data.get("main", {}).get("temp"),
                "humidity": data.get("main", {}).get("humidity"),
                "rainfall": data.get("rain", {}).get("1h", 0)
            }
    except Exception:
        pass
    return {"temperature": None, "humidity": None, "rainfall": None}

def enrich_df_with_realtime_weather(df: pd.DataFrame):
    df["rt_temperature"] = None
    df["rt_humidity"] = None
    df["rt_rainfall"] = None
    for idx, row in df.iterrows():
        lat, lon = extract_lat_lon_from_wkt(str(row.get("location_geometry", "")))
        if lat is not None and lon is not None:
            w = fetch_realtime_weather(lat, lon)
            df.at[idx, "rt_temperature"] = w["temperature"]
            df.at[idx, "rt_humidity"] = w["humidity"]
            df.at[idx, "rt_rainfall"] = w["rainfall"]
    return df

# -------------------------------
# Historical Weather Query
# -------------------------------
def fetch_weather_history(plot_id, planting_date, harvest_date):
    conn = get_connection()
    query = f"""
        SELECT record_date, rainfall_mm, temperature_c, humidity
        FROM WeatherRecord
        WHERE plot_id = '{plot_id}'
          AND record_date BETWEEN '{planting_date}' AND '{harvest_date}'
        ORDER BY record_date ASC
    """
    weather_df = pd.read_sql(query, conn)
    conn.close()
    return weather_df