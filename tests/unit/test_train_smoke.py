import os

import pytest

from mlops.config import REPO_ROOT
from mlops.train import run_training


@pytest.mark.skipif(
    not (REPO_ROOT / ".data" / "adult.data").exists(),
    reason="dataset not downloaded",
)
def test_smoke_train_local() -> None:
    os.environ["MLFLOW_DISABLED"] = "1"
    run_id = run_training(REPO_ROOT / "configs" / "smoke.yaml")
    assert run_id
    assert (REPO_ROOT / "model.pkl").exists()
