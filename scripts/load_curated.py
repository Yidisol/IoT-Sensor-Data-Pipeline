import shutil
import pandas as pd
from sqlalchemy import create_engine
from common import CURATED, RAW

src = CURATED / "final_ml_ready.parquet"
df = pd.read_parquet(src)

partitioned = CURATED / "partitioned"
if partitioned.exists():
    shutil.rmtree(partitioned)
partitioned.mkdir(parents=True, exist_ok=True)

df.to_parquet(
    partitioned,
    engine="pyarrow",
    partition_cols=["reading_date"],
    index=False,
)

df.to_csv(CURATED / "final_ml_ready.csv", index=False)

engine = create_engine(f"sqlite:///{RAW / 'sensors.db'}")
df.to_sql("sensor_readings_curated", engine, if_exists="replace", index=False)

alerts = df[df["ml_anomaly"].eq(1)][
    ["timestamp", "sensor_id", "reading_value", "z_score", "anomaly_score"]
].copy()
alerts["alert"] = "SENSOR_ANOMALY"
alerts.to_sql("anomaly_alerts", engine, if_exists="replace", index=False)

print(f"Curated rows: {len(df):,}")
print(f"Partitioned Parquet: {partitioned}")
print("SQLite tables updated: sensor_readings_curated, anomaly_alerts")
