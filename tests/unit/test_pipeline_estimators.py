import pandas as pd

from mlops.metrics import encode_labels
from mlops.models.pipeline import build_model_pipeline, feature_columns


def _fixture(rows: int = 120) -> pd.DataFrame:
    values = {
        "age": [25 + i % 40 for i in range(rows)],
        "workclass": [f"class-{i % 3}" for i in range(rows)],
        "fnlwgt": [100_000 + i for i in range(rows)],
        "education": [f"edu-{i % 4}" for i in range(rows)],
        "education-num": [8 + i % 8 for i in range(rows)],
        "marital-status": [f"status-{i % 3}" for i in range(rows)],
        "occupation": [f"job-{i % 5}" for i in range(rows)],
        "relationship": [f"rel-{i % 3}" for i in range(rows)],
        "race": [f"race-{i % 2}" for i in range(rows)],
        "sex": ["Male" if i % 2 else "Female" for i in range(rows)],
        "capital-gain": [i % 7 for i in range(rows)],
        "capital-loss": [i % 5 for i in range(rows)],
        "hours-per-week": [35 + i % 20 for i in range(rows)],
        "native-country": [f"country-{i % 3}" for i in range(rows)],
        "income": [">50K" if i % 2 else "<=50K" for i in range(rows)],
    }
    return pd.DataFrame(values)


def test_hist_gradient_boosting_full_config_fits_and_predicts() -> None:
    frame = _fixture()
    model = build_model_pipeline({"type": "hist_gradient_boosting", "max_iter": 5})
    model.fit(frame[feature_columns()], encode_labels(frame["income"]))
    predictions = model.predict(frame[feature_columns()])
    assert len(predictions) == len(frame)


def test_logistic_regression_keeps_sparse_preprocessing_contract() -> None:
    model = build_model_pipeline({"type": "logistic_regression", "max_iter": 5})
    encoder = model.named_steps["preprocess"].named_transformers_["cat"].named_steps["onehot"]
    assert encoder.sparse_output is True
