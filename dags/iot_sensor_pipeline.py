from datetime import datetime, timedelta
from pathlib import Path
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = Path("/opt/iot_sensor_pipeline")

default_args = {
    "owner": "iot-project",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="iot_sensor_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 8, 1),
    schedule="*/15 * * * *",
    catchup=False,
    tags=["iot", "sensor", "anomaly"],
) as dag:

    extract = BashOperator(
        task_id="extract_uci_csv",
        bash_command=f"python {PROJECT}/scripts/extract_uci.py",
    )

    stream = BashOperator(
        task_id="simulate_streams",
        bash_command=(
            f"python {PROJECT}/scripts/simulate_http_stream.py --records 1000 && "
            f"python {PROJECT}/scripts/mqtt_stream.py --mode file --records 1000"
        ),
    )

    raw = BashOperator(
        task_id="load_raw_sqlite_parquet",
        bash_command=f"python {PROJECT}/scripts/load_raw.py",
    )

    clean = BashOperator(
        task_id="clean_and_normalize",
        bash_command=f"python {PROJECT}/scripts/clean_normalize.py",
    )

    polars = BashOperator(
        task_id="polars_sliding_windows_and_features",
        bash_command=f"python {PROJECT}/scripts/feature_engineering_polars.py",
    )

    spark = BashOperator(
        task_id="pyspark_sliding_window",
        bash_command=f"python {PROJECT}/scripts/feature_engineering_pyspark.py",
    )

    validate = BashOperator(
        task_id="great_expectations_validation",
        bash_command=f"python {PROJECT}/quality/run_validation.py",
    )

    anomaly = BashOperator(
        task_id="anomaly_detection_and_alerts",
        bash_command=f"python {PROJECT}/scripts/anomaly_detection.py",
    )

    curated = BashOperator(
        task_id="curated_sqlite_and_partitioned_parquet",
        bash_command=f"python {PROJECT}/scripts/load_curated.py",
    )

    dvc = BashOperator(
        task_id="dvc_checkpoint",
        bash_command=(
            f"cd {PROJECT} && python {PROJECT}/scripts/setup_dvc.py --check"
        ),
    )

    alert = BashOperator(
        task_id="alerting",
        bash_command=(
            f"python -c \"from pathlib import Path; "
            f"p=Path('{PROJECT}/reports/anomaly_alerts.csv'); "
            f"print('ALERT: anomaly file ready' if p.exists() else 'No alert file')\""
        ),
        trigger_rule="all_done",
    )

    extract >> stream >> raw >> clean >> polars >> spark >> anomaly >> validate >> curated >> dvc >> alert
