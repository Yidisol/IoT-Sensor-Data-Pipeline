from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated" / "final_ml_ready.parquet"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

df = pd.read_parquet(CURATED)
x = df[df["sensor_id"].eq("S01")].sort_values("timestamp").tail(3000)

plt.figure(figsize=(14, 5))
plt.plot(x["timestamp"], x["reading_value"], label="reading_value")
plt.plot(x["timestamp"], x["rolling_avg"], label="rolling_avg")
a = x[x["anomaly_flag"].eq(1)]
plt.scatter(a["timestamp"], a["reading_value"], s=12, label="rule anomaly")
plt.title("S01 Raw Reading vs Rolling Average")
plt.xlabel("Time")
plt.ylabel("Sensor signal")
plt.legend()
plt.tight_layout()
plt.savefig(REPORTS / "raw_vs_rolling_avg.png", dpi=150)
plt.close()

corr = df.pivot_table(
    index="timestamp", columns="sensor_id", values="reading_value"
).corr()

plt.figure(figsize=(9, 7))
plt.imshow(corr, aspect="auto")
plt.colorbar(label="Correlation")
plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
plt.yticks(range(len(corr.index)), corr.index)
plt.title("Cross-Sensor Correlation Heatmap")
plt.tight_layout()
plt.savefig(REPORTS / "correlation_heatmap.png", dpi=150)
plt.close()

print("Reports generated.")
