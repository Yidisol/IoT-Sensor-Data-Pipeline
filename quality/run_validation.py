import json
from pathlib import Path
import pandas as pd
import great_expectations as gx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated" / "final_ml_ready.parquet"
OUT = ROOT / "quality" / "validation_report.json"

df = pd.read_parquet(DATA)

# Great Expectations 1.x supports an in-memory pandas source through the context.
context = gx.get_context()
datasource = context.data_sources.add_pandas(name="sensor_runtime")
data_asset = datasource.add_dataframe_asset(name="sensor_data")
batch_definition = data_asset.add_batch_definition_whole_dataframe("current_batch")
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

expectations = [
    ("sensor_id_non_null", batch.validate(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="sensor_id")
    )),
    ("timestamp_non_null", batch.validate(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="timestamp")
    )),
    ("reading_range", batch.validate(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="reading_value", min_value=-5000, max_value=70000
        )
    )),
    ("reading_value_non_null", batch.validate(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="reading_value")
    )),
    ("normalized_range", batch.validate(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="reading_normalized", min_value=0, max_value=1
        )
    )),
    ("anomaly_binary", batch.validate(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="anomaly_flag", value_set=[0, 1]
        )
    )),
]

# Additional consistency checks not expressed only as GX expectations.
duplicate_count = int(df.duplicated(["sensor_id", "timestamp"]).sum())
sensor_count = int(df["sensor_id"].nunique())
missing_rate = float(df["reading_value"].isna().mean())

results = []
success = True
for name, result in expectations:
    ok = bool(result.success)
    success = success and ok
    results.append({
        "name": name,
        "success": ok,
        "result": result.to_json_dict(),
    })

consistency_ok = duplicate_count == 0 and sensor_count == 16
success = success and consistency_ok

report = {
    "success": success,
    "row_count": len(df),
    "sensor_count": sensor_count,
    "missing_rate": missing_rate,
    "duplicate_sensor_timestamp_rows": duplicate_count,
    "consistency_ok": consistency_ok,
    "expectations": results,
}

OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

print(json.dumps({
    "success": success,
    "rows": len(df),
    "sensors": sensor_count,
    "missing_rate": missing_rate,
    "duplicates": duplicate_count,
}, indent=2))

if not success:
    raise SystemExit("Great Expectations / consistency validation failed.")
