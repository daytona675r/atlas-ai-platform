from pathlib import Path


WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "train.yml"


def test_full_train_fails_closed_and_publishes_only_after_validation() -> None:
    workflow = WORKFLOW.read_text()
    assert "set -euo pipefail" in workflow
    assert "python -m mlops.cli train --config configs/full.yaml > train-output.txt" in workflow
    assert "RUN_ID=$(tail -n 1 train-output.txt)" in workflow
    assert "[[ ! \"$RUN_ID\" =~ ^[0-9a-f]{32}$ ]]" in workflow
    assert "test -s model.pkl" in workflow
    assert "always()" not in workflow
