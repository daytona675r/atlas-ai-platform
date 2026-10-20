from __future__ import annotations

import argparse
import os
import sys

import mlflow
from mlflow.tracking import MlflowClient

from mlops.config import REPO_ROOT
from mlops.train import run_training
from mlops.validation.validate_data import main as validate_data_main
from mlops.validation.validate_run import main as validate_run_main


def cmd_validate_data(args: argparse.Namespace) -> int:
    sys.argv = ["validate_data", "--config", args.config, "--mode", args.mode]
    return validate_data_main()


def cmd_train(args: argparse.Namespace) -> int:
    run_id = run_training(args.config)
    print(run_id)
    return 0


def cmd_validate_run(args: argparse.Namespace) -> int:
    sys.argv = ["validate_run", "--run-id", args.run_id]
    return validate_run_main()


def cmd_mlflow_ping(_: argparse.Namespace) -> int:
    if os.getenv("MLFLOW_DISABLED", "").lower() in ("1", "true", "yes"):
        print("MLFLOW_DISABLED set; skip")
        return 0
    uri = os.getenv("MLFLOW_TRACKING_URI")
    if not uri:
        print("MLFLOW_TRACKING_URI not set", file=sys.stderr)
        return 1
    mlflow.set_tracking_uri(uri)
    client = MlflowClient()
    client.search_experiments(max_results=1)
    print("MLflow OK")
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    thresholds_path = REPO_ROOT / "configs" / "validation_thresholds.yaml"
    import yaml

    with thresholds_path.open(encoding="utf-8") as f:
        thresholds = yaml.safe_load(f)
    model_name = thresholds["registry_model_name"]
    result = mlflow.register_model(f"runs:/{args.run_id}/model", model_name)
    client = MlflowClient()
    client.set_registered_model_alias(model_name, "staging", result.version)
    print(f"registered {model_name} v{result.version} as staging")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mlops")
    sub = parser.add_subparsers(dest="command", required=True)

    p_data = sub.add_parser("validate-data")
    p_data.add_argument("--config", default=str(REPO_ROOT / "configs" / "data_manifest.yaml"))
    p_data.add_argument("--mode", choices=["smoke", "full"], required=True)
    p_data.set_defaults(func=cmd_validate_data)

    p_train = sub.add_parser("train")
    p_train.add_argument("--config", required=True)
    p_train.set_defaults(func=cmd_train)

    p_run = sub.add_parser("validate-run")
    p_run.add_argument("--run-id", required=True)
    p_run.set_defaults(func=cmd_validate_run)

    p_ping = sub.add_parser("mlflow-ping")
    p_ping.set_defaults(func=cmd_mlflow_ping)

    p_reg = sub.add_parser("register")
    p_reg.add_argument("--run-id", required=True)
    p_reg.set_defaults(func=cmd_register)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
