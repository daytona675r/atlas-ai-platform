# Terraform — MLOps Showcase

## Layout

- `backend.tf` — HCP Terraform remote state (edit `organization` / `workspace`)
- `oidc_github.tf` — GitHub OIDC provider + IAM role
- `modules/storage` — optional S3 artifacts bucket
- `envs/showcase` — showcase environment wiring

## Bootstrap

1. Create a free [HCP Terraform](https://app.terraform.io) organization and workspace `mlops-showcase`.
2. Update `backend.tf` with your organization name.
3. Copy `envs/showcase/terraform.tfvars.example` → `terraform.tfvars` (local only, gitignored).
4. Apply OIDC (from repo root or `infra/terraform`):

```bash
cd infra/terraform
terraform init
terraform apply -var="github_org=YOUR_ORG" -var="github_repo=mlops"
```

5. Add GitHub secret `AWS_ROLE_ARN` from output `github_actions_role_arn`.

## Optional S3

Set `enable_storage = true` in `envs/showcase/terraform.tfvars` after OIDC role exists.

## CI

`terraform-plan.yml` runs `terraform plan` on PRs when `infra/**` changes.

Use OIDC in workflow:

```yaml
permissions:
  id-token: write
  contents: read
```

## Validate locally

```bash
cd infra/terraform/envs/showcase
terraform init -backend=false
terraform validate
```
