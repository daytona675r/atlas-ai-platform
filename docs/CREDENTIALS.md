# Credentials & OIDC Runbook

## GitHub Repository Secrets

| Secret | Used by | Purpose |
|--------|---------|---------|
| `MLFLOW_TRACKING_URI` | smoke, train | DagsHub MLflow endpoint |
| `MLFLOW_TRACKING_USERNAME` | smoke, train | DagsHub user |
| `MLFLOW_TRACKING_PASSWORD` | smoke, train | DagsHub token |
| `HF_TOKEN` | deploy | Hugging Face API |
| `AWS_ROLE_ARN` | terraform | OIDC assumable role (optional S3) |

## GitHub Variables

| Variable | Example |
|----------|---------|
| `HF_SPACE_REPO` | `your-user/adult-income-api` |
| `HF_SPACE_URL` | `https://your-user-adult-income-api.hf.space` |
| `MLFLOW_REGISTRY_MODEL` | `adult-income` |

`HF_SPACE_REPO`, `HF_SPACE_URL` and `HF_TOKEN` are required for the hosted
deployment stage. Until they are configured and a hosted run is verified, the
deployment workflow records an explicit skipped state; no public endpoint is
assumed.

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
