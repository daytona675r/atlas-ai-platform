#!/usr/bin/env bash
set -euo pipefail

echo "== Atlas portfolio acceptance =="

ruff check src tests
ruff format --check src tests
mypy src/mlops
python -m mlops.cli validate-data --mode smoke

# Keep the repository's intended 70% coverage bar. Do not lower this in CI.
MLFLOW_DISABLED=1 pytest tests/unit tests/contract \
  --cov=mlops \
  --cov-report=term-missing \
  --cov-fail-under=70

docker build -f docker/Dockerfile.train -t atlas-acceptance-train .
docker run --rm --entrypoint python atlas-acceptance-train -c "import mlops"

rm -f model.pkl
MLFLOW_DISABLED=1 python -m mlops.cli train --config configs/smoke.yaml
test -s model.pkl
sha256sum model.pkl

echo "Atlas application acceptance passed."
