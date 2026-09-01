from pathlib import Path
import polars as pl
import pandas as pd
from common import CLEANED, CURATED

src = CLEANED / "sensor_readings_cleaned.parquet"
out = CURATED / "features_polars.parquet"

df = pl.read_parquet(src).sort(["sensor_id", "timestamp"])

# Time features
df = df.with_columns([
    pl.col("timestamp").dt.hour().alias("hour_of_day"),
    (pl.col("timestamp").dt.weekday() >= 6).cast(pl.Int8).alias("is_weekend"),
])

# Sliding windows / temporal features.
df = df.with_columns([
    pl.col("reading_value").rolling_mean(window_size=30, min_samples=1)
      .over("sensor_id").alias("rolling_avg"),
    pl.col("reading_value").rolling_std(window_size=30, min_samples=2)
      .over("sensor_id").alias("moving_std"),
    pl.col("reading_value").shift(1).over("sensor_id").alias("lag_1"),
    pl.col("reading_value").shift(5).over("sensor_id").alias("lag_5"),
    pl.col("reading_value").rolling_min(window_size=30, min_samples=1)
      .over("sensor_id").alias("rolling_min"),
    pl.col("reading_value").rolling_max(window_size=30, min_samples=1)
      .over("sensor_id").alias("rolling_max"),
])

df = df.with_columns([
    (
        (pl.col("reading_value") - pl.col("rolling_avg")) /
        pl.col("moving_std").replace(0, None)
    ).fill_nan(0).fill_null(0).alias("z_score"),
    (
        pl.col("reading_value") -
        pl.col("reading_value").shift(1).over("sensor_id")
    ).alias("rate_of_change"),
])

# Peak frequency: count values above the rolling mean + 1 std in each 30-row window.
df = df.with_columns([
    (
        pl.col("reading_value") >
        (pl.col("rolling_avg") + pl.col("moving_std").fill_null(0))
    ).cast(pl.Int8).rolling_sum(window_size=30, min_samples=1)
    .over("sensor_id").fill_null(0).alias("peak_frequency"),
])

# Stability score: inverse of local variation, bounded approximately 0..1.
df = df.with_columns([
    (1 / (1 + pl.col("moving_std").fill_null(0).abs())).alias("stability_score"),
])

# Rule-based anomaly flag, ±3.5 rolling z-score.
df = df.with_columns([
    (pl.col("z_score").abs() > 3.5).cast(pl.Int8).alias("anomaly_flag")
])

# Cross-sensor correlation is calculated per timestamp across S01-S16.
pdf = df.to_pandas()
pivot = pdf.pivot_table(index="timestamp", columns="sensor_id", values="reading_normalized")
corr = pivot.T.corr().mean(axis=1) if not pivot.empty else pd.Series(dtype=float)
# A per-row global correlation proxy: correlation of that timestamp's sensor vector
# with the average sensor vector.
mean_vector = pivot.mean(axis=0) if not pivot.empty else pd.Series(dtype=float)
sensor_corr = {}
if not pivot.empty:
    for ts, row in pivot.iterrows():
        valid = row.notna() & mean_vector.notna()
        if valid.sum() >= 2:
            c = row[valid].corr(mean_vector[valid])
        else:
            c = 0.0
        sensor_corr[ts] = 0.0 if pd.isna(c) else float(c)

pdf["sensor_correlation"] = pdf["timestamp"].map(sensor_corr).fillna(0.0).astype("float32")

# Estimated regression target. This is intentionally labeled as an estimate.
sensor_mean = pdf.groupby("timestamp")["reading_normalized"].transform("mean")
pdf["gas_concentration_est"] = (sensor_mean * 100.0).astype("float32")

# Ensure final schema.
feature_cols = [
    "rolling_avg", "z_score", "anomaly_flag", "hour_of_day", "is_weekend",
    "sensor_correlation", "moving_std", "peak_frequency", "rate_of_change",
    "stability_score", "lag_1", "lag_5", "rolling_min", "rolling_max"
]
pdf["reading_date"] = pd.to_datetime(pdf["timestamp"], utc=True).dt.strftime("%Y-%m-%d")

pdf.to_parquet(out, index=False)
print(f"Polars feature rows: {len(pdf):,}")
print(f"Engineered features: {len(feature_cols)}")
print(f"Saved: {out}")
