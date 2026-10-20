from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mlops.models.pipeline import feature_columns

app = FastAPI(title="Adult Income API", version="0.1.0")

_model = None


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
    global _model
    if _model is not None:
        return _model
    model_uri = os.getenv("MODEL_URI")
    model_path = os.getenv("MODEL_PATH", "model.pkl")
    if model_uri:
        _model = mlflow.sklearn.load_model(model_uri)
    elif Path(model_path).exists():
        _model = joblib.load(model_path)
    else:
        raise RuntimeError("No MODEL_URI or MODEL_PATH configured")
    return _model


@app.on_event("startup")  # noqa: E402
def startup() -> None:
    load_model()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
