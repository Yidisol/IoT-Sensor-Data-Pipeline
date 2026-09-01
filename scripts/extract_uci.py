from pathlib import Path
import time
import pandas as pd
from ucimlrepo import fetch_ucirepo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

OUT = RAW / "uci_gas_sensor_array.csv"

print("Downloading UCI Gas Sensor Array Drift dataset...")
last_error = None
for attempt in range(3):
    try:
        dataset = fetch_ucirepo(id=270)
        X = dataset.data.features.copy()
        y = dataset.data.targets.copy()

        # Preserve the original UCI columns in a portable CSV.
        raw = pd.concat([X, y], axis=1)
        raw.to_csv(OUT, index=False)

        print(f"Saved: {OUT}")
        print(f"Rows: {len(raw):,}")
        print(f"Columns: {len(raw.columns):,}")
        print(f"Feature columns: {len(X.columns):,}")
        print(f"Target columns: {len(y.columns):,}")
        break
    except Exception as exc:
        last_error = exc
        print(f"Attempt {attempt + 1}/3 failed: {exc}")
        time.sleep(2)
else:
    raise RuntimeError(f"Could not download UCI dataset: {last_error}")
