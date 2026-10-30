from pathlib import Path


def test_hist_gradient_boosting_mlflow_logging_has_explicit_trusted_types() -> None:
    source = (Path(__file__).parents[2] / "src" / "mlops" / "train.py").read_text()
    assert '"skops_trusted_types"' in source
    assert "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor" in source
