#!/usr/bin/env bash
set -euo pipefail

# Smoke CI is deliberately credential-free.  The optional MLflow ping is the
# only remote connectivity check; mini-training must exercise local artifacts.
export MLFLOW_DISABLED=1
rm -f model.pkl

PYTHON_BIN="${PYTHON_BIN:-python}"
TRAIN_OUTPUT="${TRAIN_OUTPUT:-train-output.txt}"
"$PYTHON_BIN" -m mlops.cli train --config configs/smoke.yaml > "$TRAIN_OUTPUT"
RUN_ID="$(tail -n 1 "$TRAIN_OUTPUT")"
if [[ "$RUN_ID" != "local-run" ]]; then
  echo "Smoke mini-train did not return local-run: '$RUN_ID'" >&2
  exit 1
fi
test -s model.pkl
if [[ -n "${GITHUB_ENV:-}" ]]; then
  echo "RUN_ID=$RUN_ID" >> "$GITHUB_ENV"
fi
echo "Smoke mini-train succeeded: RUN_ID=$RUN_ID artifact=model.pkl"
