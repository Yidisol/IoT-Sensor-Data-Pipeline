# Report / Topic 8 Alignment

## Data sources
1. UCI Gas Sensor Array Drift dataset.
2. Simulated HTTP sensor stream.
3. Simulated MQTT sensor stream.

## Storage
- Raw CSV
- Raw Parquet
- SQLite
- Cleaned Parquet
- Curated Parquet partitioned by `reading_date`

## Cleaning
- Parse and standardize timestamps.
- Remove duplicate `(sensor_id, timestamp)` rows.
- Impute only short missing runs up to 3 readings.
- Detect outliers using a 30-reading rolling z-score.
- Use ±3.5 as the anomaly/outlier threshold.
- Min-Max normalize each sensor.

## Engineered features
1. rolling_avg
2. z_score
3. anomaly_flag
4. hour_of_day
5. is_weekend
6. sensor_correlation
7. moving_std
8. peak_frequency
9. rate_of_change
10. stability_score
11. lag_1
12. lag_5
13. rolling_min
14. rolling_max

## Target
Primary target: binary anomaly detection.

Secondary target:
`gas_concentration_est`, an explicitly estimated regression target derived from normalized sensor signals.

## Validation
Great Expectations validates:
- non-null identifiers/timestamps
- reading range
- missingness
- normalized range
- binary anomaly flag

Additional consistency checks validate:
- exactly 16 canonical sensors
- no duplicate sensor/timestamp records

## Processing
- Polars: sliding-window feature engineering.
- PySpark: rolling window aggregations.

## Orchestration
Airflow runs the complete pipeline every 15 minutes and includes an alerting task.

## Versioning
DVC tracks raw/cleaned/curated datasets and Git tracks pipeline code/configuration.
