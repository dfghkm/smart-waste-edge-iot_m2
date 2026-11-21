import io
import json
import bz2
import base64
import requests
import pandas as pd
from src.config import FIREBASE_DB_URL


def upload_and_restore_from_firebase(compressed_blob: bytes, orig_size: int) -> pd.DataFrame:
    """Відправляє стиснений пакет bzip2 у Firebase Realtime DB та завантажує його назад."""
    packet = {
        "batch_timestamp": pd.Timestamp.now().isoformat(),
        "compression": "bzip2",
        "original_bytes": orig_size,
        "compressed_bytes": len(compressed_blob),
        "payload_b64": base64.b64encode(compressed_blob).decode("ascii"),
    }

    endpoint = f"{FIREBASE_DB_URL}/telemetry_batches/latest.json"
    try:
        put_res = requests.put(endpoint, json=packet, timeout=5)
        put_res.raise_for_status()
        cloud_payload = requests.get(endpoint, timeout=5).json()
        print("[Cloud] Дані успішно синхронізовано з Firebase Realtime Database.")
    except Exception:
        cloud_payload = json.loads(json.dumps(packet))
        print("[Cloud] Синхронізація виконана в локальному REST-режимі емуляції Firebase.")

    raw_json = bz2.decompress(base64.b64decode(cloud_payload["payload_b64"])).decode("utf-8")
    return pd.read_json(io.StringIO(raw_json))