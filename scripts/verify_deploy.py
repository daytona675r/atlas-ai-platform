#!/usr/bin/env python3
"""VAL-L4 deploy verification against running serve container."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.getenv("SERVE_URL", "http://localhost:8000")
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "predict_request.json"
BATCH = REPO_ROOT / "tests" / "fixtures" / "predict_batch.json"


def check(condition: bool, vid: str, msg: str) -> None:
    if not condition:
        raise SystemExit(f"{vid}: {msg}")


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        r = client.get("/health")
        check(r.status_code == 200 and r.json().get("status") == "ok", "VAL-L4-03", r.text)

        r = client.get("/model-info")
        check(r.status_code == 200, "VAL-L4-04", r.text)
        info = r.json()
        for env_name, field in (("EXPECTED_COMMIT_SHA", "commit_sha"),
                                ("EXPECTED_SOURCE_RUN_ID", "source_run_id"),
                                ("EXPECTED_MLFLOW_RUN_ID", "run_id"),
                                ("EXPECTED_MODEL_SHA256", "model_sha256")):
            expected = os.getenv(env_name)
            if expected:
                check(info.get(field) == expected, "VAL-L4-04", f"{field} provenance mismatch")

        payload = json.loads(FIXTURE.read_text())
        r = client.post("/predict", json=payload)
        check(r.status_code == 200, "VAL-L4-05", r.text)
        body = r.json()
        check(body["prediction"] in ("<=50K", ">50K"), "VAL-L4-06", str(body))
        check(0 <= body["probability"] <= 1, "VAL-L4-06", "probability")

        batch = json.loads(BATCH.read_text())
        r = client.post("/predict/batch", json=batch)
        check(r.status_code == 200 and len(r.json()) == 10, "VAL-L4-07", r.text)

        r = client.post("/predict", json={"bad": True})
        check(r.status_code == 422, "VAL-L4-08", str(r.status_code))

        latencies = []
        for _ in range(10):
            t0 = time.perf_counter()
            client.post("/predict", json=payload)
            latencies.append(time.perf_counter() - t0)
        latencies.sort()
        p95 = latencies[int(0.95 * len(latencies)) - 1]
        check(p95 < 0.5, "VAL-L4-09", f"p95={p95}")

    print("VAL-L4 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
