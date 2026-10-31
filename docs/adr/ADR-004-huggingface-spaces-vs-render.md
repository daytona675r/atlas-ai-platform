# ADR-004: Render Free for hosted inference

## Status

Accepted

## Context

Need free-tier hosting for FastAPI inference after VAL-L4.

## Decision

**Primary:** Render web service on the free plan. The existing service is
`atlas-ai-platform-demo` in Frankfurt and is deployed through an owner-only
Render deploy hook after the candidate has passed local validation.

## Rationale

Render builds the exact pinned `render-release` branch, which contains the
validated source snapshot plus `model.pkl` and `candidate-metadata.json`. The
service keeps auto-deploy disabled; the workflow controls release timing and
then verifies the public endpoint with Layer 4 checks.

## Consequences

- `deploy.yml` updates the release branch and calls `RENDER_DEPLOY_HOOK`.
- `MODEL_URI` env points to MLflow registry staging/production aliases.
