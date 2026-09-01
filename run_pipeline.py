import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Extract UCI CSV", ["scripts/extract_uci.py"]),
    ("Generate HTTP stream", ["scripts/simulate_http_stream.py", "--records", "1000"]),
    ("Generate MQTT simulation file", ["scripts/mqtt_stream.py", "--mode", "file", "--records", "1000"]),
    ("Load raw storage", ["scripts/load_raw.py"]),
    ("Clean and normalize", ["scripts/clean_normalize.py"]),
    ("Polars feature engineering", ["scripts/feature_engineering_polars.py"]),
    ("Isolation Forest and alerts", ["scripts/anomaly_detection.py"]),
    ("Great Expectations validation", ["quality/run_validation.py"]),
    ("Load curated data", ["scripts/load_curated.py"]),
    ("Generate reports", ["scripts/generate_reports.py"]),
]

def run_step(name, command):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    result = subprocess.run([sys.executable, *command], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {name}")

def main():
    parser = argparse.ArgumentParser(description="Run the Topic 8 IoT sensor pipeline.")
    parser.add_argument("--skip-spark", action="store_true", help="Skip the optional PySpark implementation.")
    parser.add_argument("--skip-dvc", action="store_true", help="Skip DVC initialization/tracking.")
    args = parser.parse_args()

    for name, command in STEPS:
        run_step(name, command)

    if not args.skip_spark:
        try:
            run_step("PySpark sliding-window aggregation", ["scripts/feature_engineering_pyspark.py"])
        except SystemExit:
            print("PySpark failed. Re-run with --skip-spark if Java/Spark is unavailable.")
            raise

    if not args.skip_dvc:
        run_step("DVC initialization and dataset tracking", ["scripts/setup_dvc.py"])

    print("\nPipeline completed successfully.")
    print(f"Project output: {ROOT}")

if __name__ == "__main__":
    main()
