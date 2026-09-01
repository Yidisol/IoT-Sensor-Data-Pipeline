import numpy as np
import pandas as pd
from common import RAW, CLEANED

src = RAW / "sensor_readings.parquet"
out = CLEANED / "sensor_readings_cleaned.parquet"

df = pd.read_parquet(src)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
df = df.dropna(subset=["sensor_id", "timestamp"])
df = df.drop_duplicates(["sensor_id", "timestamp"], keep="last")
df = df.sort_values(["sensor_id", "timestamp"]).reset_index(drop=True)

df["is_imputed"] = 0

# Fill only short missing runs (<=3) within each sensor.
for sensor, idx in df.groupby("sensor_id").groups.items():
    idx = list(idx)
    values = df.loc[idx, "reading_value"].copy()
    missing = values.isna()
    groups = missing.ne(missing.shift()).cumsum()
    gap_size = missing.groupby(groups).transform("sum")
    short_gap = missing & (gap_size <= 3)
    filled = values.ffill()
    df.loc[idx, "reading_value"] = values.where(~short_gap, filled)
    df.loc[idx, "is_imputed"] = short_gap.astype("int8").values

g = df.groupby("sensor_id")["reading_value"]
df["rolling_avg"] = g.transform(lambda s: s.rolling(30, min_periods=5).mean())
df["moving_std"] = g.transform(lambda s: s.rolling(30, min_periods=5).std())
z = (df["reading_value"] - df["rolling_avg"]) / df["moving_std"].replace(0, np.nan)
df["outlier_flag"] = z.abs().gt(3.5).fillna(False).astype("int8")

def minmax(s):
    lo, hi = s.min(), s.max()
    if pd.notna(lo) and pd.notna(hi) and hi != lo:
        return (s - lo) / (hi - lo)
    return pd.Series(0.0, index=s.index)

df["reading_normalized"] = (
    df.groupby("sensor_id")["reading_value"].transform(minmax).astype("float32")
)
df["reading_date"] = df["timestamp"].dt.strftime("%Y-%m-%d")

df.to_parquet(out, index=False)
print(f"Cleaned rows: {len(df):,}")
print(f"Missing after short-gap imputation: {df.reading_value.isna().mean():.2%}")
print(f"Outliers: {int(df.outlier_flag.sum()):,}")
print(f"Saved: {out}")
