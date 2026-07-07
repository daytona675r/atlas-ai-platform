# ADR-004: Hugging Face Spaces vs Render

## Status

Accepted

## Context

Need free-tier hosting for FastAPI inference after VAL-L4.

## Decision

**Primary:** Hugging Face Spaces (Docker SDK). **Alternative:** Render web service (documented in deploy workflow comments).

## Rationale

HF Spaces integrates with `HF_TOKEN`, public demo URL, strong ML portfolio signal.

## Consequences

- `deploy.yml` pushes/updates Space via `huggingface_hub` or documented manual hook.
- `MODEL_URI` env points to MLflow registry staging/production aliases.
