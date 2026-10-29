"""Fail-closed validation for an artifact from one successful Full Train run."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def validate_candidate(
    run: dict[str, Any], metadata: dict[str, Any], model_bytes: bytes, requested_run_id: str
) -> None:
    if str(run.get("id")) != requested_run_id:
        raise ValueError("resolved run ID does not match requested run ID")
    valid_run = (
        run.get("name") == "Full Train"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    )
    if not valid_run:
        raise ValueError("source run is not a successful Full Train run")
    commit_sha = metadata.get("commit_sha")
    if not isinstance(commit_sha, str) or not FULL_SHA.fullmatch(commit_sha):
        raise ValueError("candidate commit SHA must be a full immutable SHA")
    if commit_sha != run.get("head_sha"):
        raise ValueError("candidate commit does not match source run head SHA")
    if str(metadata.get("source_run_id")) != requested_run_id:
        raise ValueError("candidate metadata source run ID mismatch")
    if metadata.get("source_workflow") != "Full Train":
        raise ValueError("candidate metadata workflow mismatch")
    if not metadata.get("run_id"):
        raise ValueError("MLflow run ID is required")
    actual_sha = hashlib.sha256(model_bytes).hexdigest()
    if metadata.get("model_sha256") != actual_sha:
        raise ValueError("candidate model SHA-256 mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-json", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--requested-run-id", required=True)
    args = parser.parse_args()
    run = json.loads(args.run_json.read_text())
    metadata = json.loads(args.metadata.read_text())
    validate_candidate(run, metadata, args.model.read_bytes(), args.requested_run_id)
    print(json.dumps({"commit_sha": metadata["commit_sha"], "run_id": metadata["run_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
