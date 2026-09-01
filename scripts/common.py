from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
CLEANED = DATA / "cleaned"
CURATED = DATA / "curated"
STREAM = DATA / "stream"
REPORTS = ROOT / "reports"
QUALITY = ROOT / "quality"
MODELS = ROOT / "models"

SENSORS = [f"S{i:02d}" for i in range(1, 17)]

for p in [RAW, CLEANED, CURATED, STREAM, REPORTS, QUALITY, MODELS]:
    p.mkdir(parents=True, exist_ok=True)

def parse_uci_value(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    if ":" in text:
        text = text.rsplit(":", 1)[-1]
    try:
        return float(text)
    except ValueError:
        return np.nan

def canonicalize_uci_csv(csv_path):
    raw = pd.read_csv(csv_path)

    target_names = [c for c in raw.columns if c.lower() in {"class", "target"}]
    feature_columns = [c for c in raw.columns if c not in target_names]

    parsed = raw[feature_columns].apply(lambda s: s.map(parse_uci_value))
    numeric_columns = [c for c in parsed.columns if parsed[c].notna().any()]

    if len(numeric_columns) < 16:
        raise ValueError(
            f"UCI file has only {len(numeric_columns)} usable numeric columns; "
            "at least 16 are required."
        )

    # The UCI Gas Sensor Array Drift dataset packs 8 heterogeneous features
    # per sensor (steady-state resistance-change DR, |DR|, and 6 EMA transient
    # coefficients at different smoothing values). These are different
    # physical quantities on very different scales, so averaging all 8
    # together produces a meaningless composite value. Instead, take only
    # the first feature in each 8-column block: the steady-state DR reading,
    # which is the closest analogue to a single physical sensor reading.
    groups = np.array_split(numeric_columns, 16)
    wide = pd.DataFrame(index=parsed.index)

    for sensor, cols in zip(SENSORS, groups):
        wide[sensor] = parsed[list(cols)[0]]

    for sensor in SENSORS:
        wide[sensor] = (
            wide[sensor]
            .replace([np.inf, -np.inf], np.nan)
            .astype("float64")
        )

    # Give historical observations deterministic timestamps.
    wide["timestamp"] = pd.date_range(
        "2025-01-01 00:00:00",
        periods=len(wide),
        freq="min",
        tz="UTC",
    )
    wide["source"] = "batch"
    return wide

def wide_to_long(wide, batch_id):
    df = wide.melt(
        id_vars=["timestamp", "source"],
        value_vars=SENSORS,
        var_name="sensor_id",
        value_name="reading_value",
    )
    df["gas_type"] = "mixed"
    df["unit"] = "sensor_signal"
    df["reading_value"] = pd.to_numeric(df["reading_value"], errors="coerce").astype("float32")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["ingestion_timestamp"] = pd.Timestamp.now(tz="UTC")
    df["load_batch_id"] = batch_id
    return df[
        ["sensor_id", "timestamp", "reading_value", "gas_type", "unit",
         "source", "ingestion_timestamp", "load_batch_id"]
    ].copy()

def read_stream_jsonl(path):
    rows = []
    if not path.exists():
        return pd.DataFrame()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        return pd.DataFrame()
    wide = pd.DataFrame(rows)
    wide["timestamp"] = pd.to_datetime(wide["timestamp"], utc=True, errors="coerce")
    for s in SENSORS:
        if s in wide.columns:
            wide[s] = pd.to_numeric(wide[s], errors="coerce")
    return wide
