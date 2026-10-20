from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from mlops.config import REPO_ROOT, file_sha256, load_yaml
from mlops.data.loaders import download_dataset, load_adult_dataframe
from mlops.data.split import split_dataframe
from mlops.models.pipeline import feature_columns


class ValidationError(Exception):
    pass


def _check(condition: bool, check_id: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{check_id}: {message}")


def validate_layer1(manifest_path: Path, mode: str) -> pd.DataFrame:
    cfg = load_yaml(manifest_path)
    cache = download_dataset(manifest_path)
    _check(cache.exists(), "VAL-L1-01", f"cache missing at {cache}")

    digest = file_sha256(cache)
    _check(digest == cfg["sha256"], "VAL-L1-02", f"sha256 mismatch expected {cfg['sha256']}")

    df = load_adult_dataframe(manifest_path)
    _check(len(df) > 0, "VAL-L1-03", "empty dataframe")

    expected = cfg["columns"]
    _check(list(df.columns) == expected, "VAL-L1-04", f"columns {list(df.columns)}")
    _check(len(df.columns) == len(set(df.columns)), "VAL-L1-05", "duplicate columns")

    if mode == "smoke":
        smoke_cfg = load_yaml(REPO_ROOT / "configs" / "smoke.yaml")
        max_rows = int(smoke_cfg.get("max_rows", 1000))
        df = df.sample(n=min(max_rows, len(df)), random_state=42).reset_index(drop=True)
        row_min, row_max = cfg["row_count"]["smoke_min"], cfg["row_count"]["smoke_max"]
        minority_min = cfg["minority_class_min"]["smoke"]
        miss_cap = cfg["missing_rate_max"]["smoke_any_feature"]
    else:
        row_min, row_max = cfg["row_count"]["full_min"], cfg["row_count"]["full_max"]
        minority_min = cfg["minority_class_min"]["full"]
        miss_cap = None

    _check(
        row_min <= len(df) <= row_max,
        "VAL-L1-06",
        f"row count {len(df)} not in [{row_min},{row_max}]",
    )

    target = cfg["target"]
    labels = df[target].astype(str).str.strip()
    allowed = {"<=50K", ">50K"}
    _check(
        set(labels.unique()).issubset(allowed),
        "VAL-L1-07",
        f"invalid labels {set(labels.unique())}",
    )
    _check(
        labels.notna().all() and (labels != "").all(),
        "VAL-L1-08",
        "empty targets",
    )

    pos_rate = (labels == cfg["positive_label"]).mean()
    min_rate = min(pos_rate, 1 - pos_rate)
    _check(min_rate >= minority_min, "VAL-L1-09", f"minority rate {min_rate}")

    _check(df["age"].between(17, 90).all(), "VAL-L1-10", "age out of range")
    _check(df["hours-per-week"].between(1, 99).all(), "VAL-L1-11", "hours-per-week out of range")
    _check((df["education-num"] >= 0).all(), "VAL-L1-12", "education-num invalid")

    features = feature_columns()
    for col in features:
        rate = df[col].isna().mean()
        cap = miss_cap
        if mode == "full" and col == "native-country":
            cap = cfg["missing_rate_max"]["full_native_country"]
        elif mode == "full":
            cap = cfg["missing_rate_max"]["full_default"]
        _check(
            rate <= cap,
            "VAL-L1-13",
            f"{col} missing rate {rate} > {cap}",
        )
        _check(
            not df[col].isna().all(),
            "VAL-L1-14",
            f"{col} all null",
        )

    for col in features:
        numeric_columns = {
            "age",
            "fnlwgt",
            "education-num",
            "capital-gain",
            "capital-loss",
            "hours-per-week",
        }
        if col in numeric_columns:
            _check(df[col].nunique(dropna=True) > 1, "VAL-L1-15", f"{col} constant")
        else:
            _check(df[col].nunique(dropna=True) > 1, "VAL-L1-15", f"{col} constant cat")
        if col not in numeric_columns:
            _check(df[col].nunique(dropna=True) <= 100, "VAL-L1-16", f"{col} cardinality")

    feature_hash = df[features].astype(str).agg("|".join, axis=1)
    _check(not feature_hash.duplicated().any(), "VAL-L1-17", "duplicate feature rows")

    train_df, val_df, test_df = split_dataframe(
        df,
        target=target,
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1,
        random_state=42,
    )
    train_keys = set(train_df[features].astype(str).agg("|".join, axis=1))
    test_keys = set(test_df[features].astype(str).agg("|".join, axis=1))
    _check(train_keys.isdisjoint(test_keys), "VAL-L1-18", "train/test overlap")

    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "data_manifest.yaml"))
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    args = parser.parse_args(argv)
    try:
        validate_layer1(Path(args.config), args.mode)
        print(f"VAL-L1 passed ({args.mode})")
        return 0
    except ValidationError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
