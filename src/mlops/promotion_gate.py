from __future__ import annotations

import argparse
import sys
from typing import Any

from mlflow.tracking import MlflowClient

from mlops.config import REPO_ROOT, load_yaml


def load_thresholds() -> dict[str, Any]:
    return load_yaml(REPO_ROOT / "configs" / "validation_thresholds.yaml")


def get_champion_f1(client: MlflowClient, model_name: str) -> float | None:
    try:
        versions = client.get_latest_versions(model_name, stages=["Production", "Staging"])
        if not versions:
            return None
        version = versions[0]
        run = client.get_run(version.run_id)
        return float(run.data.metrics.get("test_f1", 0.0))
    except Exception:
        return None


def check_champion(run_id: str, thresholds: dict[str, Any]) -> tuple[bool, str]:
    client = MlflowClient()
    run = client.get_run(run_id)
    new_f1 = float(run.data.metrics.get("test_f1", 0.0))
    model_name = thresholds["registry_model_name"]
    champion = get_champion_f1(client, model_name)
    delta = thresholds.get("champion_improvement_min", 0.0)
    if champion is None:
        return True, "no champion; gate passes"
    if new_f1 >= champion - delta:
        return True, f"new f1 {new_f1:.4f} >= champion {champion:.4f} - {delta}"
    return False, f"new f1 {new_f1:.4f} < champion {champion:.4f} - {delta}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    thresholds = load_thresholds()
    ok, msg = check_champion(args.run_id, thresholds)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
