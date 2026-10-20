import json
import os

import pytest
from fastapi.testclient import TestClient

from mlops.config import REPO_ROOT
from mlops.serving.app import app
from mlops.train import run_training


@pytest.fixture
def client() -> TestClient:
    os.environ["MLFLOW_DISABLED"] = "1"
    if not (REPO_ROOT / "model.pkl").exists():
        run_training(REPO_ROOT / "configs" / "smoke.yaml")
    os.environ["MODEL_PATH"] = str(REPO_ROOT / "model.pkl")
    os.environ.pop("MODEL_URI", None)
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_predict(client: TestClient) -> None:
    payload = json.loads((REPO_ROOT / "tests" / "fixtures" / "predict_request.json").read_text())
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] in ("<=50K", ">50K")
    assert 0 <= body["probability"] <= 1


def test_predict_batch(client: TestClient) -> None:
    payload = json.loads((REPO_ROOT / "tests" / "fixtures" / "predict_batch.json").read_text())
    r = client.post("/predict/batch", json=payload)
    assert r.status_code == 200
    assert len(r.json()) == 10


def test_predict_invalid(client: TestClient) -> None:
    r = client.post("/predict", json={"age": 10})
    assert r.status_code == 422
