from __future__ import annotations

import pytest

from mlops.config import REPO_ROOT
from mlops.data.loaders import download_dataset


@pytest.fixture(scope="session", autouse=True)
def ensure_dataset() -> None:
    cache = REPO_ROOT / ".data" / "adult.data"
    if not cache.exists():
        try:
            download_dataset()
        except Exception:
            fixture = REPO_ROOT / "tests" / "fixtures" / "adult_sample.csv"
            if fixture.exists():
                cache.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy(fixture, cache)
