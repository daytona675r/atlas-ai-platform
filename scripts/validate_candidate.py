"""Fail-closed validation for an artifact from one successful Full Train run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mlops.candidate_validation import validate_candidate


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
