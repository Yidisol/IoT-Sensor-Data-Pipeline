from pathlib import Path
from flask import Flask, jsonify, request
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stream" / "http_received.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

@app.post("/sensor")
def sensor():
    payload = request.get_json(force=True)
    payload["_received_at"] = datetime.now(timezone.utc).isoformat()
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    return jsonify(status="received")

@app.get("/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    print("HTTP IoT API: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
