from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from mlops.config import REPO_ROOT, load_yaml
from mlops.metrics import encode_labels
from mlops.models.pipeline import feature_columns
from mlops.promotion_gate import check_champion


class RunValidationError(Exception):
    pass


def _check(condition: bool, check_id: str, message: str) -> None:
    if not condition:
        raise RunValidationError(f"{check_id}: {message}")


def validate_layer3(run_id: str) -> None:
    thresholds = load_yaml(REPO_ROOT / "configs" / "validation_thresholds.yaml")
    client = MlflowClient()
    run = client.get_run(run_id)
    _check(run.info.status == "FINISHED", "VAL-L3-01", f"status {run.info.status}")

    metrics = run.data.metrics
    for key in ("test_accuracy", "test_f1", "test_roc_auc"):
        _check(key in metrics, "VAL-L3-02", f"missing {key}")

    _check(metrics["test_accuracy"] >= thresholds["test_accuracy_min"], "VAL-L3-03", "accuracy low")
    _check(metrics["test_f1"] >= thresholds["test_f1_min"], "VAL-L3-04", "f1 low")
    _check(metrics["test_roc_auc"] >= thresholds["test_roc_auc_min"], "VAL-L3-05", "roc_auc low")

    gap = metrics.get("train_accuracy", 0) - metrics.get("val_accuracy", 0)
    _check(gap <= thresholds["train_val_accuracy_gap_max"], "VAL-L3-06", f"overfit gap {gap}")

    model_uri = f"runs:/{run_id}/model"
    model = mlflow.sklearn.load_model(model_uri)
    _check(model is not None, "VAL-L3-09", "model load failed")

    test_path = REPO_ROOT / "test.parquet"
    if test_path.exists():
        test_df = pd.read_parquet(test_path)
        features = feature_columns()
        x_test = test_df[features]
        y_test = encode_labels(test_df["income"])
        pred = model.predict(x_test)
        proba = model.predict_proba(x_test)[:, 1]
        _check((pred == 1).any() and (pred == 0).any(), "VAL-L3-07", "single class predictions")
        pos_rate = float(proba.mean())
        _check(
            thresholds["test_positive_rate_min"] <= pos_rate <= thresholds["test_positive_rate_max"],
            "VAL-L3-08",
            f"pos rate {pos_rate}",
        )
        acc = accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred)
        auc = roc_auc_score(y_test, proba)
        eps = thresholds["metric_reproducibility_epsilon"]
        _check(abs(acc - metrics["test_accuracy"]) <= eps, "VAL-L3-10", "accuracy mismatch")
        _check(abs(f1 - metrics["test_f1"]) <= eps, "VAL-L3-10", "f1 mismatch")
        _check(abs(auc - metrics["test_roc_auc"]) <= eps, "VAL-L3-10", "auc mismatch")

    params = run.data.params
    for p in ("data_sha256", "config_hash", "git_sha"):
        _check(p in params, "VAL-L3-12", f"missing param {p}")

    _check("income" not in feature_columns(), "VAL-L3-13", "target in features")

    ok, msg = check_champion(run_id, thresholds)
    _check(ok, "VAL-L3-11", msg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        validate_layer3(args.run_id)
        print("VAL-L3 passed")
        return 0
    except RunValidationError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
