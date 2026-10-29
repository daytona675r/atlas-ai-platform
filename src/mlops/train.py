from __future__ import annotations

import os
import subprocess
from pathlib import Path

import joblib
import mlflow
from mlflow.models import infer_signature

from mlops.config import REPO_ROOT, file_sha256, load_yaml
from mlops.data.clean import cleaned_data_fingerprint, deduplicate_feature_vectors
from mlops.data.loaders import download_dataset, load_adult_dataframe
from mlops.data.split import split_dataframe
from mlops.metrics import compute_metrics, encode_labels
from mlops.models.pipeline import build_model_pipeline, feature_columns


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def run_training(config_path: Path | str) -> str:
    cfg = load_yaml(config_path)
    manifest = load_yaml(REPO_ROOT / "configs" / "data_manifest.yaml")
    cache = download_dataset()
    data_sha = file_sha256(cache)

    max_rows = cfg.get("max_rows") if cfg.get("mode") == "smoke" else None
    df = load_adult_dataframe(max_rows=max_rows)
    target = manifest["target"]
    df = deduplicate_feature_vectors(df, feature_columns())
    cleaned_data_sha = cleaned_data_fingerprint(df)
    train_df, val_df, test_df = split_dataframe(
        df,
        target=target,
        train_ratio=cfg["train_ratio"],
        val_ratio=cfg["val_ratio"],
        test_ratio=cfg["test_ratio"],
        random_state=cfg["random_state"],
    )

    features = feature_columns()
    pipeline = build_model_pipeline(cfg["model"])
    x_train, y_train = train_df[features], encode_labels(train_df[target])
    x_val, y_val = val_df[features], encode_labels(val_df[target])
    x_test, y_test = test_df[features], encode_labels(test_df[target])

    pipeline.fit(x_train, y_train)

    train_pred = pipeline.predict(x_train)
    val_pred = pipeline.predict(x_val)
    test_pred = pipeline.predict(x_test)
    train_proba = pipeline.predict_proba(x_train)[:, 1]
    val_proba = pipeline.predict_proba(x_val)[:, 1]
    test_proba = pipeline.predict_proba(x_test)[:, 1]

    train_m = compute_metrics(y_train, train_pred, train_proba)
    val_m = compute_metrics(y_val, val_pred, val_proba)
    test_m = compute_metrics(y_test, test_pred, test_proba)

    test_path = REPO_ROOT / "test.parquet"
    test_df.to_parquet(test_path, index=False)
    model_path = REPO_ROOT / "model.pkl"
    joblib.dump(pipeline, model_path)

    mlflow_disabled = os.getenv("MLFLOW_DISABLED", "").lower() in ("1", "true", "yes")
    run_id = "local-run"
    if not mlflow_disabled:
        mlflow.set_experiment(cfg["mlflow"]["experiment_name"])
        with mlflow.start_run() as run:
            run_id = run.info.run_id
            mlflow.log_params(
                {
                    "mode": cfg.get("mode", "unknown"),
                    "data_sha256": data_sha,
                    "cleaned_data_sha256": cleaned_data_sha,
                    "config_hash": file_sha256(Path(config_path)),
                    "git_sha": _git_sha(),
                    "random_state": cfg["random_state"],
                    "max_rows": max_rows or "all",
                }
            )
            for prefix, metrics in [
                ("train", train_m),
                ("val", val_m),
                ("test", test_m),
            ]:
                for k, v in metrics.items():
                    mlflow.log_metric(f"{prefix}_{k}", v)
            signature = infer_signature(x_test, test_pred)
            mlflow.sklearn.log_model(
                pipeline,
                artifact_path="model",
                signature=signature,
                input_example=x_test.head(5),
            )
            mlflow.log_artifact(str(test_path), artifact_path="data")
    return run_id
