#!/usr/bin/env python3
"""Fail-closed validation of the exact Smoke CI prerequisite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mlops.smoke_validation import select_exact_smoke_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-json", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    args = parser.parse_args()
    data = json.loads(args.runs_json.read_text())
    selected = select_exact_smoke_run(data.get("workflow_runs", data), args.commit_sha)
    print(json.dumps({"id": selected["id"], "head_sha": selected["head_sha"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
