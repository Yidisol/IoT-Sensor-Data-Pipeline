import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from common import STREAM, SENSORS

TOPIC = "iot/sensors/gas"

def make_payload(i, ts, rng):
    p = {"timestamp": ts.isoformat(), "source": "mqtt_stream"}
    for j, s in enumerate(SENSORS):
        value = 100 + j * 15 + np.sin(i / 50) * 10 + rng.normal(0, 3)
        if i in {100, 250, 400, 650, 800}:
            value += rng.normal(60, 10)
        if rng.random() < 0.01:
            value = None
        p[s] = None if value is None else float(value)
    return p

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["file", "publisher", "server"], default="file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    if args.mode == "file":
        out = STREAM / "mqtt_stream.jsonl"
        rng = np.random.default_rng(123)
        start = pd.Timestamp.now(tz="UTC").floor("min")
        with out.open("w", encoding="utf-8") as f:
            for i, ts in enumerate(pd.date_range(start, periods=args.records, freq="min", tz="UTC")):
                f.write(json.dumps(make_payload(i, ts, rng)) + "\n")
                if args.delay:
                    time.sleep(args.delay)
        print(f"Saved MQTT simulation file: {out}")
        return

    import paho.mqtt.client as mqtt

    if args.mode == "server":
        received = STREAM / "mqtt_received.jsonl"
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        def on_message(client, userdata, msg):
            with received.open("a", encoding="utf-8") as f:
                f.write(msg.payload.decode("utf-8") + "\n")
        client.on_message = on_message
        client.connect(args.host, args.port, 60)
        client.subscribe(TOPIC)
        print(f"Listening on mqtt://{args.host}:{args.port}/{TOPIC}")
        client.loop_forever()

    if args.mode == "publisher":
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(args.host, args.port, 60)
        client.loop_start()
        rng = np.random.default_rng(123)
        start = pd.Timestamp.now(tz="UTC").floor("min")
        for i, ts in enumerate(pd.date_range(start, periods=args.records, freq="min", tz="UTC")):
            client.publish(TOPIC, json.dumps(make_payload(i, ts, rng)), qos=1)
            if args.delay:
                time.sleep(args.delay)
        client.loop_stop()
        client.disconnect()
        print("MQTT publisher finished.")

if __name__ == "__main__":
    main()
