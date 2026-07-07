# ADR-001: GitHub Actions vs TeamCity

## Status

Accepted

## Context

Prior experience used TeamCity for CV model validate/train/test/measure pipelines. This repo is a public portfolio showcase.

## Decision

Use **GitHub Actions** as the sole CI/CD orchestrator.

## Rationale

- Zero license cost for public repos; workflows are pipeline-as-code in Git.
- Recruiters and agents inspect `.github/workflows/` directly.
- Native integration with OIDC, environments, and secrets.

## Consequences

- TeamCity is documented as prior art only; not configured in this repo.
