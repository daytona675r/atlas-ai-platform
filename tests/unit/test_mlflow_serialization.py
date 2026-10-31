import tempfile

import mlflow.sklearn
import pandas as pd

from mlops.models.pipeline import build_model_pipeline, feature_columns


def _training_frame() -> tuple[pd.DataFrame, list[int]]:
    rows = []
    labels = []
    for index in range(12):
        row = {column: 1 for column in feature_columns()}
        for column in [
            "workclass",
            "education",
            "marital-status",
            "occupation",
            "relationship",
            "race",
            "sex",
            "native-country",
        ]:
            row[column] = f"value-{index % 3}"
        rows.append(row)
        labels.append(index % 2)
    return pd.DataFrame(rows), labels


def test_configured_estimators_round_trip_through_mlflow_save_model() -> None:
    frame, labels = _training_frame()
    for model_cfg, trusted_types in [
        ({"type": "logistic_regression", "max_iter": 50}, []),
        (
            {"type": "hist_gradient_boosting", "max_iter": 5},
            [
                "numpy.dtype",
                "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
            ],
        ),
    ]:
        pipeline = build_model_pipeline(model_cfg).fit(frame, labels)
        with tempfile.TemporaryDirectory() as model_dir:
            kwargs = {"skops_trusted_types": trusted_types} if trusted_types else {}
            mlflow.sklearn.save_model(pipeline, path=model_dir, **kwargs)
            loaded = mlflow.sklearn.load_model(model_dir)
            assert list(loaded.predict(frame)) == list(pipeline.predict(frame))
