from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import requests

from mlops.config import REPO_ROOT, load_yaml


def _manifest_path(manifest: Path | str | None) -> Path:
    if manifest is None:
        return REPO_ROOT / "configs" / "data_manifest.yaml"
    return Path(manifest)


def download_dataset(manifest: Path | str | None = None, force: bool = False) -> Path:
    cfg = load_yaml(_manifest_path(manifest))
    cache = REPO_ROOT / cfg["cache_path"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists() and not force:
        return cache
    resp = requests.get(cfg["url"], timeout=120)
    resp.raise_for_status()
    cache.write_bytes(resp.content)
    return cache


def load_adult_dataframe(
    manifest: Path | str | None = None,
    max_rows: int | None = None,
    cache_only: bool = False,
) -> pd.DataFrame:
    cfg = load_yaml(_manifest_path(manifest))
    cache = REPO_ROOT / cfg["cache_path"]
    fixture = REPO_ROOT / "tests" / "fixtures" / "adult_sample.csv"
    if not cache.exists():
        if cache_only and fixture.exists():
            cache = fixture
        else:
            download_dataset(manifest)
    df = pd.read_csv(
        cache,
        header=None,
        names=cfg["columns"],
        skipinitialspace=True,
        na_values=["?"],
    )
    df["income"] = df["income"].astype(str).str.strip()
    if max_rows is not None:
        df = df.sample(n=min(max_rows, len(df)), random_state=42)
    return df.reset_index(drop=True)
