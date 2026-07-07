# ADR-003: OIDC vs Long-Lived AWS Keys

## Status

Accepted

## Context

GitHub Actions must access AWS for Terraform apply and optional S3 without storing static credentials.

## Decision

Use **GitHub OIDC** → `aws_iam_openid_connect_provider` → IAM role with least-privilege policies.

## Rationale

Short-lived tokens; no rotation of access keys in secrets.

## Consequences

- `terraform-plan.yml` / apply use `aws-actions/configure-aws-credentials` with `role-to-assume`.
- DagsHub and Hugging Face still use repository secrets (no OIDC on those platforms in v1).
