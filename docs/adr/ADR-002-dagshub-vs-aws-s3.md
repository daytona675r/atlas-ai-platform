# ADR-002: DagsHub vs AWS S3 for Artifacts

## Status

Accepted (hybrid)

## Context

Need hosted MLflow and artifact storage without operating servers.

## Decision

- **Primary:** DagsHub hosted MLflow + S3-compatible artifact store (free tier).
- **Optional:** AWS S3 via Terraform `modules/storage` for extra IaC demonstration (ADR-002 optional path).

## Rationale

DagsHub eliminates MLflow server ops. Terraform S3 module still proves IaC + OIDC for job narrative.

## Consequences

- Training logs to `MLFLOW_TRACKING_URI` from GitHub Secrets.
- S3 module defaults `enable_storage = false` in showcase env until operator opts in.
