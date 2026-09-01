from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "raw" / "sensors.db"

st.set_page_config(page_title="Industrial IoT Sensor Monitoring", layout="wide")
st.title("Industrial IoT Gas Sensor Monitoring")

if not DB.exists():
    st.error("Database not found. Run: python run_pipeline.py --skip-spark")
    st.stop()

engine = create_engine(f"sqlite:///{DB}")

df = pd.read_sql("SELECT * FROM sensor_readings_curated", engine)
alerts = pd.read_sql(
    "SELECT * FROM anomaly_alerts ORDER BY timestamp DESC LIMIT 100",
    engine,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Readings", f"{len(df):,}")
c2.metric("Sensors", int(df["sensor_id"].nunique()))
c3.metric("ML anomalies", int(df["ml_anomaly"].sum()))
c4.metric("Missing rate", f"{df['reading_value'].isna().mean():.2%}")

sensor = st.selectbox("Sensor", sorted(df["sensor_id"].unique()))
x = df[df["sensor_id"].eq(sensor)].sort_values("timestamp").tail(1000).copy()

st.subheader(f"{sensor} sensor signal")
chart = x.set_index("timestamp")[["reading_value", "rolling_avg"]]
st.line_chart(chart)

st.subheader("Anomaly score")
st.line_chart(x.set_index("timestamp")[["anomaly_score"]])

st.subheader("Recent alerts")
st.dataframe(alerts, use_container_width=True)

st.subheader("Feature summary")
feature_cols = [
    "rolling_avg", "z_score", "anomaly_flag", "hour_of_day",
    "is_weekend", "sensor_correlation", "moving_std",
    "peak_frequency", "rate_of_change", "stability_score",
]
st.dataframe(df[feature_cols].describe().T, use_container_width=True)
