"""Fail-closed champion comparison for the protected production alias."""

from __future__ import annotations

import argparse
import math
import sys
from typing import Any

from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from mlops.config import REPO_ROOT, load_yaml


class ChampionLookupError(RuntimeError):
    """A registry lookup failed or the champion metadata is unusable."""


def load_thresholds() -> dict[str, Any]:
    return load_yaml(REPO_ROOT / "configs" / "validation_thresholds.yaml")


def _missing_alias(error: Exception) -> bool:
    """Return true only for an explicitly absent production alias."""
    if isinstance(error, KeyError):
        return True
    if isinstance(error, MlflowException):
        error_code = getattr(error, "error_code", None)
        if error_code == "RESOURCE_DOES_NOT_EXIST":
            return True
    message = str(error).lower()
    return "alias" in message and ("not found" in message or "does not exist" in message)


def get_champion_f1(client: MlflowClient, model_name: str) -> float | None:
    """Read ``test_f1`` from the real production alias.

    ``None`` means the alias is explicitly absent, which is the documented
    first-model bootstrap policy. Connectivity, permissions and malformed
    champion metadata raise ``ChampionLookupError`` so VAL-L3-11 fails closed.
    """
    try:
        version = client.get_model_version_by_alias(model_name, "production")
    except Exception as error:  # MLflow uses several exception subclasses by version
        if _missing_alias(error):
            return None
        raise ChampionLookupError(f"production alias lookup failed: {error}") from error

    run_id = getattr(version, "run_id", None)
    if not run_id:
        raise ChampionLookupError("production alias has no run_id")
    try:
        run = client.get_run(run_id)
    except Exception as error:
        raise ChampionLookupError(f"champion run lookup failed: {error}") from error
    value = run.data.metrics.get("test_f1")
    if not isinstance(value, (int, float)):
        raise ChampionLookupError("production champion is missing test_f1")
    return float(value)


def check_champion(run_id: str, thresholds: dict[str, Any]) -> tuple[bool, str]:
    client = MlflowClient()
    try:
        run = client.get_run(run_id)
        value = run.data.metrics.get("test_f1")
        if not isinstance(value, (int, float)):
            return False, "candidate is missing test_f1"
        new_f1 = float(value)
        model_name = thresholds["registry_model_name"]
        champion = get_champion_f1(client, model_name)
    except ChampionLookupError as error:
        return False, str(error)
    except Exception as error:
        return False, f"candidate/registry lookup failed: {error}"

    if champion is None:
        return True, "no production alias; first-model bootstrap is allowed"

    delta = float(thresholds.get("champion_improvement_min", 0.0))
    required = champion + delta
    if new_f1 >= required or math.isclose(new_f1, required, abs_tol=1e-9):
        return True, f"new f1 {new_f1:.4f} >= champion {champion:.4f} + {delta:.4f}"
    return False, f"new f1 {new_f1:.4f} < champion {champion:.4f} + {delta:.4f}"


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
