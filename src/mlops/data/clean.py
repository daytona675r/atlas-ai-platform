"""Deterministic cleaning shared by validation and model training."""

from __future__ import annotations

import hashlib

import pandas as pd


def feature_duplicate_counts(df: pd.DataFrame, features: list[str]) -> tuple[int, int]:
    counts = df.groupby(features, dropna=False, sort=False).size()
    groups = int((counts > 1).sum())
    extra_rows = int((counts[counts > 1] - 1).sum())
    return groups, extra_rows


def deduplicate_feature_vectors(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Keep the first raw occurrence of each feature vector deterministically."""
    return df.drop_duplicates(subset=features, keep="first").reset_index(drop=True)


def cleaned_data_fingerprint(df: pd.DataFrame) -> str:
    csv = df.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(csv.encode()).hexdigest()
