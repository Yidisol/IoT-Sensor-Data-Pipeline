from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from common import ROOT, RAW, STREAM, SENSORS, canonicalize_uci_csv, wide_to_long, read_stream_jsonl

UCI_CSV = RAW / "uci_gas_sensor_array.csv"
DB = RAW / "sensors.db"

batch_wide = canonicalize_uci_csv(UCI_CSV)
batch = wide_to_long(batch_wide, "vscode_batch")

stream_frames = []
for name in ["http_stream.jsonl", "mqtt_stream.jsonl", "http_received.jsonl", "mqtt_received.jsonl"]:
    frame = read_stream_jsonl(STREAM / name)
    if not frame.empty:
        stream_frames.append(frame)

stream = pd.DataFrame()
if stream_frames:
    stream_wide = pd.concat(stream_frames, ignore_index=True)
    stream = wide_to_long(stream_wide, "vscode_stream")

df = pd.concat([batch, stream], ignore_index=True)
df = df.sort_values(["timestamp", "sensor_id"]).reset_index(drop=True)

csv_out = RAW / "sensor_readings.csv"
parquet_out = RAW / "sensor_readings.parquet"
df.to_csv(csv_out, index=False)
df.to_parquet(parquet_out, index=False)

engine = create_engine(f"sqlite:///{DB}")
df.to_sql("sensor_readings_raw", engine, if_exists="replace", index=False)

print(f"Raw rows: {len(df):,}")
print(f"Raw CSV: {csv_out}")
print(f"Raw Parquet: {parquet_out}")
print(f"SQLite: {DB}")
