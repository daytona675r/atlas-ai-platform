# Credentials & OIDC Runbook

## GitHub Repository Secrets

| Secret | Used by | Purpose |
|--------|---------|---------|
| `MLFLOW_TRACKING_URI` | smoke, train | DagsHub MLflow endpoint |
| `MLFLOW_TRACKING_USERNAME` | smoke, train | DagsHub user |
| `MLFLOW_TRACKING_PASSWORD` | smoke, train | DagsHub token |
| `RENDER_DEPLOY_HOOK` | deploy | Owner-only Render deploy hook for the linked service |
| `AWS_ROLE_ARN` | terraform | OIDC assumable role (optional S3) |

## GitHub Variables

| Variable | Example |
|----------|---------|
| `RENDER_SERVICE_URL` | `https://atlas-ai-platform-demo.onrender.com` |
| `RENDER_RELEASE_BRANCH` | `render-release` |
| `MLFLOW_REGISTRY_MODEL` | `adult-income` |

`RENDER_SERVICE_URL` and `RENDER_DEPLOY_HOOK` are required for the hosted
deployment stage. Configure the existing Render service
`atlas-ai-platform-demo` to track `render-release` with auto-deploy disabled.
The workflow updates that branch only after the exact Full Train candidate has
passed local validation, then invokes the owner-only hook. Until a hosted
Layer-4 run is verified, no public demo claim is made.

## Workflow injection

Workflows map secrets to environment variables:

```yaml
env:
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  MLFLOW_TRACKING_USERNAME: ${{ secrets.MLFLOW_TRACKING_USERNAME }}
  MLFLOW_TRACKING_PASSWORD: ${{ secrets.MLFLOW_TRACKING_PASSWORD }}
```

## OIDC setup (AWS)

1. Apply `infra/terraform/oidc_github.tf` + `envs/showcase` with your `github_org/repo`.
2. Add GitHub secret `AWS_ROLE_ARN` = terraform output `github_actions_role_arn`.
3. Enable `id-token: write` permission in workflows using OIDC.

See [infra/terraform/README.md](../infra/terraform/README.md).

## Local development

Set the same env vars in `.env` (gitignored). Use `MLFLOW_DISABLED=1` to skip remote tracking during unit tests.
