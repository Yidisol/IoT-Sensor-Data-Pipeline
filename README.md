# Topic 8 — IoT Sensor Data Pipeline (VS Code)

This project is a local, VS Code-friendly implementation of **Topic 8: IoT Sensor Data Pipeline**.

## What is included

- **Domain:** Industrial IoT sensor monitoring
- **Dataset:** UCI Gas Sensor Array Drift + simulated sensor streams
- **Batch ingestion:** UCI data is downloaded and converted to CSV
- **Streaming ingestion:** simulated **HTTP** and **MQTT** sensor messages
- **Storage:** SQLite + raw/cleaned/curated **Parquet partitioned by `reading_date`**
- **Cleaning:** timestamp normalization, duplicate removal, short-gap imputation, rolling outlier detection, Min-Max normalization
- **14 engineered features:** rolling average, z-score, anomaly flag, hour, weekend, sensor correlation, moving standard deviation, peak frequency, rate of change, stability score, lags, rolling min/max
- **Validation:** Great Expectations checks for range, missing rate, duplicate/consistency
- **Sliding windows:** Polars and PySpark implementations
- **Anomaly detection:** Isolation Forest + rule-based anomaly flag
- **Alerts:** CSV + SQLite alert feed
- **Dashboard:** Streamlit
- **Orchestration:** Airflow DAG
- **Dataset versioning:** DVC (automatically initialized/tracked by the pipeline)
- **Cloud bonus:** notes for AWS IoT Core/Kinesis, GCP and Azure

## 1. Prerequisites

Install:

1. Python 3.11 recommended
2. VS Code
3. VS Code Python extension
4. Git
5. Java 17+ if running the PySpark script locally
6. Optional: Docker Desktop for Airflow
7. Optional: Mosquitto if you want a real MQTT broker

Check:

```powershell
python --version
git --version
java -version
```

## 2. Open the project in VS Code

```powershell
cd iot_sensor_pipeline_vscode
code .
```

## 3. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Install Python packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Airflow is intentionally not in `requirements.txt` because Airflow is not reliably installed as a normal Windows package. Use WSL2/Docker for the Airflow part. The pipeline itself runs normally from VS Code on Windows.

## 5. Run the complete local pipeline

The simplest VS Code path is:

```powershell
python run_pipeline.py --skip-spark
```

This performs:

1. UCI extraction
2. HTTP stream simulation
3. MQTT simulation fallback
4. raw CSV/Parquet/SQLite storage
5. cleaning and outlier detection
6. feature engineering with Polars
7. PySpark sliding-window aggregation
8. Great Expectations validation
9. Isolation Forest anomaly detection
10. curated Parquet/SQLite outputs
10. curated Parquet/SQLite outputs
11. dashboard-ready reports
12. DVC initialization and dataset tracking

If you only want the core pipeline without Spark:

```powershell
python run_pipeline.py --skip-spark
```

## 6. Start the HTTP ingestion API separately

Terminal 1:

```powershell
python scripts/http_server.py
```

Terminal 2:

```powershell
python scripts/simulate_http_stream.py --url http://127.0.0.1:5000/sensor --records 100
```

The messages are saved to:

```text
data/stream/http_stream.jsonl
```

## 7. Run MQTT simulation

For a real local MQTT broker, install/start Mosquitto and use:

```powershell
python scripts/mqtt_stream.py --mode server --host 127.0.0.1 --port 1883
```

In another terminal:

```powershell
python scripts/mqtt_stream.py --mode publisher --host 127.0.0.1 --port 1883 --records 100
```

If you do not have Mosquitto, the publisher can still run in `--mode file`, which creates a simulated MQTT message file:

```powershell
python scripts/mqtt_stream.py --mode file --records 100
```

The file is:

```text
data/stream/mqtt_stream.jsonl
```

## 8. Run the dashboard

After the pipeline has completed:

```powershell
streamlit run dashboard/app.py
```

Open the URL printed by Streamlit.

## 9. Run validation manually

```powershell
python quality/run_validation.py
```

Validation output:

```text
quality/validation_report.json
```

## 10. Run Polars sliding-window processing

```powershell
python scripts/feature_engineering_polars.py
```

## 11. Run PySpark sliding-window processing

```powershell
python scripts/feature_engineering_pyspark.py
```

Output:

```text
data/curated/pyspark_windows/
```

## 12. DVC

Initialize once:

```powershell
dvc init
```

Track important datasets:

```powershell
dvc add data/raw/sensor_readings.parquet
dvc add data/cleaned/sensor_readings_cleaned.parquet
dvc add data/curated
git add .
git commit -m "Version IoT sensor pipeline datasets"
```

For a remote DVC repository, configure an S3/Azure/GCS/other supported remote separately.

## 13. Airflow

The DAG is:

```text
dags/iot_sensor_pipeline.py
```

Recommended on Windows: use Docker Desktop/WSL2.

The DAG contains:

```text
batch extraction
       +
stream simulation
       |
       v
raw SQLite + Parquet
       |
       v
clean + normalize
       |
       v
Polars feature engineering
       |
       v
PySpark sliding windows
       |
       v
Great Expectations validation
       |
       v
curated Parquet + SQLite
       |
       +----> anomaly detection ----> alerts
       |
       v
DVC versioning
       |
       v
dashboard refresh
```

The schedule is every 15 minutes.

## 14. Topic 8 requirement mapping

| Requirement | Implementation |
|---|---|
| Industrial IoT | 16 canonical sensor channels S01-S16 |
| UCI 13,000+ readings | `extract_uci.py` |
| Simulated sensor streams | HTTP + MQTT |
| CSV extraction | `data/raw/uci_gas_sensor_array.csv` |
| SQLite | `data/raw/sensors.db` |
| Parquet | raw, cleaned and partitioned curated datasets |
| Missing values | short-gap forward fill + remaining diagnostics |
| Rolling outliers | 30-reading rolling z-score, threshold 3.5 |
| Normalization | sensor-level Min-Max |
| rolling_avg | included |
| z_score | included |
| anomaly_flag | included |
| hour_of_day | included |
| is_weekend | included |
| sensor_correlation | included |
| moving_std | included |
| peak_frequency | included |
| rate_of_change | included |
| stability_score | included |
| Great Expectations | `quality/run_validation.py` |
| Polars | `feature_engineering_polars.py` |
| PySpark | `feature_engineering_pyspark.py` |
| Airflow | `dags/iot_sensor_pipeline.py` |
| Alerting | `reports/anomaly_alerts.csv` + SQLite |
| DVC | `.dvc/` + tracked data |
| Dataset for anomaly detection | `data/curated/final_ml_ready.parquet` |
| Dashboard | Streamlit |
| Cloud bonus | `docs/cloud_bonus.md` |

## Important note about the UCI dataset

The UCI Gas Sensor Array Drift dataset contains many gas-sensor measurement columns rather than exactly 16 columns named S01-S16. This implementation creates **16 canonical sensor channels by grouping the available numeric measurement columns into 16 sensor blocks and selecting the first feature from each block**, preserving a physically consistent steady-state reading for each S01-S16 channel.

The derived `gas_concentration_est` field is an **estimated regression target**, not a laboratory gas concentration measurement. The primary target used by this implementation is binary anomaly detection.

## Troubleshooting

### `java` not found

Install Java 17+ and make sure `JAVA_HOME` is configured.

### Spark fails on Windows

Use:

```powershell
python run_pipeline.py --skip-spark
```

The rest of the pipeline does not depend on Spark.

### UCI download fails

The extractor retries and reports the exact error. You need internet access for the first UCI download.

### MQTT connection refused

Start Mosquitto or use:

```powershell
python scripts/mqtt_stream.py --mode file --records 100
```

### Dashboard says database table is missing

Run:

```powershell
python run_pipeline.py --skip-spark
```

before starting Streamlit.
