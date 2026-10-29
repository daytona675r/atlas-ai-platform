"""Validation helpers for the exact successful Smoke CI prerequisite."""

from __future__ import annotations

from typing import Any


def select_exact_smoke_run(runs: list[dict[str, Any]], commit_sha: str) -> dict[str, Any]:
    matches = [
        run for run in runs
        if run.get("name") == "Smoke CI"
        and run.get("head_sha") == commit_sha
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    if not matches:
        raise ValueError(f"no successful Smoke CI run found for commit {commit_sha}")
    return sorted(matches, key=lambda run: int(run.get("id", 0)), reverse=True)[0]
