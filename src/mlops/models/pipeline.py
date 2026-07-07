from __future__ import annotations

from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def feature_columns() -> list[str]:
    return [
        "age",
        "workclass",
        "fnlwgt",
        "education",
        "education-num",
        "marital-status",
        "occupation",
        "relationship",
        "race",
        "sex",
        "capital-gain",
        "capital-loss",
        "hours-per-week",
        "native-country",
    ]


def build_model_pipeline(model_cfg: dict[str, Any]) -> Pipeline:
    numeric = ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
    categorical = [c for c in feature_columns() if c not in numeric]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    model_type = model_cfg.get("type", "logistic_regression")
    if model_type == "hist_gradient_boosting":
        clf: Any = HistGradientBoostingClassifier(
            max_iter=model_cfg.get("max_iter", 100),
            random_state=42,
        )
    else:
        clf = LogisticRegression(
            max_iter=model_cfg.get("max_iter", 200),
            random_state=42,
        )
    return Pipeline([("preprocess", preprocessor), ("classifier", clf)])
