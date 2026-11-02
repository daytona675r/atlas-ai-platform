from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
from typing import Any

import joblib
import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from mlops.models.pipeline import feature_columns

app = FastAPI(title="Adult Income API", version="0.1.0")

_LANDING_TEMPLATE = Path(__file__).with_name("index.html")

_model = None
_model_info: dict[str, str] | None = None


class PredictRequest(BaseModel):
    age: int = Field(ge=17, le=90)
    workclass: str
    fnlwgt: int
    education: str
    education_num: int = Field(alias="education-num", ge=0)
    marital_status: str = Field(alias="marital-status")
    occupation: str
    relationship: str
    race: str
    sex: str
    capital_gain: int = Field(alias="capital-gain")
    capital_loss: int = Field(alias="capital-loss")
    hours_per_week: int = Field(alias="hours-per-week", ge=1, le=99)
    native_country: str = Field(alias="native-country")

    model_config = {"populate_by_name": True}


class PredictResponse(BaseModel):
    prediction: str
    probability: float


def load_model() -> Any:
    global _model, _model_info
    if _model is not None:
        return _model
    model_uri = os.getenv("MODEL_URI")
    model_path = os.getenv("MODEL_PATH", "model.pkl")
    metadata_path = Path(os.getenv("MODEL_METADATA_PATH", "candidate-metadata.json"))
    require_metadata = os.getenv("REQUIRE_MODEL_METADATA", "0").lower() in {"1", "true", "yes"}
    if require_metadata and not metadata_path.exists():
        raise RuntimeError(f"Model provenance metadata is required: {metadata_path}")
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text())
            required = ("commit_sha", "source_run_id", "run_id", "model_sha256")
            if any(not isinstance(metadata.get(key), str) or not metadata[key] for key in required):
                raise ValueError("candidate metadata is missing required identity fields")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"Invalid model provenance metadata: {exc}") from exc
    else:
        metadata = {"mode": "local"}
    if model_uri:
        _model = mlflow.sklearn.load_model(model_uri)
    elif Path(model_path).exists():
        model_file = Path(model_path)
        _model = joblib.load(model_file)
        if metadata.get("model_sha256"):
            actual = hashlib.sha256(model_file.read_bytes()).hexdigest()
            if metadata["model_sha256"] != actual:
                raise RuntimeError("Model provenance metadata does not match model bytes")
    else:
        raise RuntimeError("No MODEL_URI or MODEL_PATH configured")
    _model_info = {str(key): str(value) for key, value in metadata.items()}
    return _model


@app.on_event("startup")  # noqa: E402
def startup() -> None:
    load_model()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _landing_value(value: object | None) -> str:
    """Return a safe display value for optional deployed provenance."""
    if value is None or not str(value).strip() or str(value) == "local":
        return "Unavailable"
    return str(value)


def _render_landing_page() -> str:
    """Render the public project page without changing the serving contracts."""
    load_model()
    info = _model_info or {}
    source_run_id = info.get("source_run_id")
    source_run_url = (
        f"https://github.com/daytona675r/atlas-ai-platform/actions/runs/{source_run_id}"
        if source_run_id and source_run_id.isdigit()
        else "https://github.com/daytona675r/atlas-ai-platform/actions/workflows/train.yml"
    )
    values = {
        "{{COMMIT_SHA}}": html.escape(_landing_value(info.get("commit_sha"))),
        "{{SOURCE_RUN_ID}}": html.escape(_landing_value(source_run_id)),
        "{{MLFLOW_RUN_ID}}": html.escape(_landing_value(info.get("run_id"))),
        "{{MODEL_SHA256}}": html.escape(_landing_value(info.get("model_sha256"))),
        "{{SOURCE_RUN_URL}}": html.escape(source_run_url, quote=True),
    }
    page = _LANDING_TEMPLATE.read_text(encoding="utf-8")
    for token, value in values.items():
        page = page.replace(token, value)
    return page


@app.get("/", response_class=HTMLResponse)
def landing_page() -> HTMLResponse:
    return HTMLResponse(_render_landing_page())


@app.get("/model-info")
def model_info() -> dict[str, str]:
    load_model()
    assert _model_info is not None
    return _model_info


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest) -> PredictResponse:
    model = load_model()
    raw = body.model_dump(by_alias=True)
    columns = feature_columns()
    frame = pd.DataFrame([[raw[col] for col in columns]], columns=columns)
    try:
        pred = model.predict(frame)[0]
        proba = float(model.predict_proba(frame)[0][1])
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    label = ">50K" if int(pred) == 1 else "<=50K"
    return PredictResponse(prediction=label, probability=proba)


@app.post("/predict/batch")
def predict_batch(rows: list[PredictRequest]) -> list[PredictResponse]:
    return [predict(r) for r in rows]
