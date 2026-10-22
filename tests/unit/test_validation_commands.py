from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from mlops import cli
from mlops.promotion_gate import check_champion, get_champion_f1
from mlops.validation import validate_data


def _frame(rows: int = 600) -> pd.DataFrame:
    values: dict[str, list[object]] = {
        "age": [25 + i % 50 for i in range(rows)],
        "workclass": [f"class-{i % 4}" for i in range(rows)],
        "fnlwgt": list(range(100_000, 100_000 + rows)),
        "education": [f"edu-{i % 5}" for i in range(rows)],
        "education-num": [8 + i % 8 for i in range(rows)],
        "marital-status": [f"status-{i % 3}" for i in range(rows)],
        "occupation": [f"job-{i % 6}" for i in range(rows)],
        "relationship": [f"rel-{i % 3}" for i in range(rows)],
        "race": [f"race-{i % 3}" for i in range(rows)],
        "sex": ["Male" if i % 2 else "Female" for i in range(rows)],
        "capital-gain": [i % 7 for i in range(rows)],
        "capital-loss": [i % 5 for i in range(rows)],
        "hours-per-week": [35 + i % 20 for i in range(rows)],
        "native-country": [f"country-{i % 4}" for i in range(rows)],
        "income": [">50K" if i % 2 else "<=50K" for i in range(rows)],
    }
    return pd.DataFrame(values)


def test_validate_layer1_smoke_is_deterministic(monkeypatch, tmp_path: Path) -> None:
    frame = _frame()
    config = {
        "sha256": "digest",
        "columns": list(frame.columns),
        "row_count": {"smoke_min": 500, "smoke_max": 2000},
        "minority_class_min": {"smoke": 0.2},
        "missing_rate_max": {"smoke_any_feature": 0.1},
        "target": "income",
        "positive_label": ">50K",
    }
    cache = tmp_path / "adult.data"
    cache.write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(validate_data, "load_yaml", lambda _: config)
    monkeypatch.setattr(validate_data, "download_dataset", lambda _: cache)
    monkeypatch.setattr(validate_data, "file_sha256", lambda _: "digest")
    monkeypatch.setattr(validate_data, "load_adult_dataframe", lambda _: frame.copy())
    monkeypatch.setattr(validate_data, "REPO_ROOT", tmp_path)
    assert len(validate_data.validate_layer1(tmp_path / "manifest.yaml", "smoke")) == 600


def test_promotion_gate_handles_missing_and_regressing_champion(monkeypatch) -> None:
    run = SimpleNamespace(data=SimpleNamespace(metrics={"test_f1": 0.8}))
    client = SimpleNamespace(
        get_run=lambda _: run,
        get_latest_versions=lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr("mlops.promotion_gate.MlflowClient", lambda: client)
    assert get_champion_f1(client, "model") is None
    assert check_champion("run", {"registry_model_name": "model"})[0]


def test_cli_dispatches_validate_data(monkeypatch) -> None:
    called: list[object] = []
    monkeypatch.setattr(cli, "validate_data_main", lambda: called.append(cli.sys.argv) or 0)
    assert cli.cmd_validate_data(Namespace(config="manifest.yaml", mode="smoke")) == 0
    assert called and "--mode" in called[0]


def test_cli_dispatches_train_and_validate_run(monkeypatch) -> None:
    monkeypatch.setattr(cli, "run_training", lambda config: "run-123")
    assert cli.cmd_train(Namespace(config="smoke.yaml")) == 0
    monkeypatch.setattr(cli, "validate_run_main", lambda: 0)
    assert cli.cmd_validate_run(Namespace(run_id="run-123")) == 0


def test_cli_main_supports_disabled_mlflow(monkeypatch) -> None:
    monkeypatch.setenv("MLFLOW_DISABLED", "1")
    assert cli.main(["mlflow-ping"]) == 0


def test_promotion_gate_rejects_regression(monkeypatch) -> None:
    challenger = SimpleNamespace(data=SimpleNamespace(metrics={"test_f1": 0.4}))
    champion_run = SimpleNamespace(data=SimpleNamespace(metrics={"test_f1": 0.8}))
    version = SimpleNamespace(run_id="champion")
    client = SimpleNamespace(
        get_run=lambda run_id: challenger if run_id == "run" else champion_run,
        get_latest_versions=lambda *_args, **_kwargs: [version],
    )
    monkeypatch.setattr("mlops.promotion_gate.MlflowClient", lambda: client)
    ok, message = check_champion(
        "run", {"registry_model_name": "model", "champion_improvement_min": 0.0}
    )
    assert not ok and "< champion" in message
