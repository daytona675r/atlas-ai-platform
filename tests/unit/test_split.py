from mlops.data.loaders import load_adult_dataframe
from mlops.data.split import split_dataframe


def test_split_disjoint() -> None:
    df = load_adult_dataframe(max_rows=2000)
    train, val, test = split_dataframe(df, "income", 0.8, 0.1, 0.1, 42)
    assert len(train) + len(val) + len(test) == len(df)
    train_keys = set(train.astype(str).apply(lambda row: "|".join(map(str, row.tolist())), axis=1))
    test_keys = set(test.astype(str).apply(lambda row: "|".join(map(str, row.tolist())), axis=1))
    assert train_keys.isdisjoint(test_keys)
