import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from common import ROOT, SENSORS, STREAM

def make_payload(i, ts, rng):
    payload = {"timestamp": ts.isoformat(), "source": "http_stream"}
    for j, sensor in enumerate(SENSORS):
        value = 100 + j * 15 + np.sin(i / 50) * 10 + rng.normal(0, 3)
        if i in {100, 250, 400, 650, 800}:
            value += rng.normal(60, 10)
        if rng.random() < 0.01:
            value = None
        payload[sensor] = None if value is None else float(value)
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5000/sensor")
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--send-http", action="store_true")
    args = parser.parse_args()

    out = STREAM / "http_stream.jsonl"
    rng = np.random.default_rng(42)
    start = pd.Timestamp.now(tz="UTC").floor("min")
    sent = 0

    with out.open("w", encoding="utf-8") as f:
        for i, ts in enumerate(pd.date_range(start, periods=args.records, freq="min", tz="UTC")):
            payload = make_payload(i, ts, rng)
            f.write(json.dumps(payload) + "\n")
            if args.send_http:
                response = requests.post(args.url, json=payload, timeout=5)
                response.raise_for_status()
                sent += 1
            if args.delay:
                time.sleep(args.delay)

    print(f"Saved simulated HTTP stream: {out}")
    print(f"Records: {args.records:,}; HTTP records sent: {sent:,}")

if __name__ == "__main__":
    main()
