from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "data/raw/sensor_readings.parquet",
    ROOT / "data/cleaned/sensor_readings_cleaned.parquet",
    ROOT / "data/curated/final_ml_ready.parquet",
    ROOT / "data/raw/sensors.db",
    ROOT / "models/isolation_forest.joblib",
    ROOT / "reports/anomaly_alerts.csv",
    ROOT / "quality/validation_report.json",
]
missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing outputs:\n" + "\n".join(missing))
df=pd.read_parquet(ROOT/"data/curated/final_ml_ready.parquet")
validation=json.loads((ROOT/"quality/validation_report.json").read_text())
assert len(df)==len(df.drop_duplicates(["sensor_id","timestamp"]))
assert df["sensor_id"].nunique()==16
assert validation["success"] is True
print(f"Verification passed: {len(df):,} curated rows, 16 sensors, validation success=True.")
