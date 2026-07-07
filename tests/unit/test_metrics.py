import numpy as np

from mlops.metrics import compute_metrics


def test_compute_metrics() -> None:
    y = np.array([0, 1, 1, 0])
    pred = np.array([0, 1, 0, 0])
    proba = np.array([0.1, 0.9, 0.4, 0.2])
    m = compute_metrics(y, pred, proba)
    assert 0 <= m["accuracy"] <= 1
    assert 0 <= m["f1"] <= 1
    assert 0 <= m["roc_auc"] <= 1
