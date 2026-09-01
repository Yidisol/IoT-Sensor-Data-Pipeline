from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from common import CURATED, REPORTS, MODELS

src = CURATED / "features_polars.parquet"
out = CURATED / "final_ml_ready.parquet"

df = pd.read_parquet(src)

model_features = [
    "reading_value", "rolling_avg", "moving_std", "z_score",
    "rate_of_change", "sensor_correlation", "stability_score",
    "lag_1", "lag_5", "peak_frequency"
]
X = df[model_features].replace([np.inf, -np.inf], np.nan).fillna(0)

model = IsolationForest(
    n_estimators=150,
    contamination=0.03,
    random_state=42,
    n_jobs=-1,
)
pred = model.fit_predict(X)
df["ml_anomaly"] = (pred == -1).astype("int8")
df["anomaly_score"] = -model.score_samples(X)

alerts = df.loc[
    df["ml_anomaly"].eq(1),
    ["timestamp", "sensor_id", "reading_value", "z_score", "anomaly_score"]
].copy()
alerts["alert"] = "SENSOR_ANOMALY"
alerts = alerts.sort_values("timestamp", ascending=False)

alerts.to_csv(REPORTS / "anomaly_alerts.csv", index=False)
joblib.dump(model, MODELS / "isolation_forest.joblib")
df.to_parquet(out, index=False)

print(f"ML anomaly rate: {df.ml_anomaly.mean():.2%}")
print(f"Alerts: {len(alerts):,}")
print(f"Saved: {out}")
