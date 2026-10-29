---
doc_id: mlops-system-spec
version: 0.3.0
status: active
hosting_model: cloud_native_free_tier
primary_use_case: tabular_classification_uci_adult
mlflow_host: dagshub
validation_layers: 4
---

# MLOps System Specification

## goals {#goals}

- Cloud-native MLOps showcase: CI/CD, IaC, validation gates, MLflow registry, deploy-verify.
- Reproducible smoke vs full training on UCI Adult (tabular classification).
- Free-tier discipline: GitHub Actions, DagsHub MLflow, HCP Terraform, optional AWS S3 via OIDC.
- Agent- and human-readable: stable IDs (`FR-*`, `VAL-L*-*`), configs in Git.

## non_goals {#non_goals}

- Local MLflow/MinIO as required infrastructure.
- SOTA models, proprietary data, 24/7 production SLAs.
- GPU training (v2 / CIFAR-10 only).

## requirements {#requirements}

### Functional

| ID | Requirement |
|----|-------------|
| FR-001 | Reproducible training from pinned config + `random_state` |
| FR-002 | VAL-L1 + VAL-L2 in `smoke.yml`; failure blocks CI |
| FR-003 | Full train; VAL-L3 required before MLflow registration |
| FR-004 | VAL-L3 registers `@staging`; hosted VAL-L4 is required before `@production` |
| FR-005 | Champion comparison (VAL-L3-11) |
| FR-006 | Terraform state on HCP; AWS via OIDC only |
| FR-007 | CD to Hugging Face Spaces after VAL-L4 |

### Non-functional

| ID | Requirement |
|----|-------------|
| NFR-001 | Smoke (L1+L2) &lt; 10 min on `ubuntu-latest` |
| NFR-002 | No secrets in repo; DagsHub/HF via GitHub Secrets |
| NFR-003 | Every validation check has stable `VAL-L*-*` ID |
| NFR-004 | $0 monthly at idle |
| NFR-005 | Fork + secrets only — no local install required |
| NFR-006 | Thresholds in `configs/validation_thresholds.yaml` |

## tool_matrix {#tool_matrix}

| Tool | Role | Cost | Path |
|------|------|------|------|
| GitHub Actions | CI/CD | Free (public) | `.github/workflows/` |
| DagsHub | MLflow + artifacts | Free tier | Secrets |
| Terraform + HCP | IaC state | Free tier | `infra/terraform/` |
| AWS S3 (optional) | Extra storage | Free tier 12mo | `modules/storage` |
| Docker | Train/serve images | Free in CI | `docker/` |
| sklearn / pandas | ML + data | OSS | `src/mlops/` |
| Hugging Face Spaces | Serving | Free tier | `deploy.yml` |

## architecture {#architecture}

See [README.md](../README.md) for the diagram. Flow: PR → `smoke.yml` (L1,L2) → `train.yml` (L1, train, L3, register `@staging`) → `deploy.yml` (exact Smoke prerequisite, local L4, HF hosted L4).

## pipelines {#pipelines}

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `smoke.yml` | PR, push `main`, `v*` tags, manual | VAL-L1 → VAL-L2 |
| `train.yml` | `v*` tags, manual | VAL-L1 → train → VAL-L3 → register `@staging` |
| `deploy.yml` | after train, manual | VAL-L4 → HF deploy → VAL-L4 preflight → `@production` |
| `terraform-plan.yml` | PR touching `infra/**` | `fmt`, `init -backend=false`, `validate` |

## validation {#validation}

Gate rules:

| Failure | Blocks |
|---------|--------|
| L1 or L2 | CI build |
| L3 | Registration / `@staging` |
| L4 | Hosted deployment verification (when HF configuration is present) |
| L4 preflight | `@staging` → `@production` |

### Layer 1 — Data (`validate_data.py`)

| ID | Check |
|----|-------|
| VAL-L1-01 | Cache file exists |
| VAL-L1-02 | SHA256 matches manifest |
| VAL-L1-03 | Parseable CSV |
| VAL-L1-04 | Column set exact (14 features + income) |
| VAL-L1-05 | No duplicate column names |
| VAL-L1-06 | Row count in band (smoke/full) |
| VAL-L1-07 | Target in {<=50K, >50K} |
| VAL-L1-08 | No empty targets |
| VAL-L1-09 | Minority class prevalence |
| VAL-L1-10 | age 17–90 |
| VAL-L1-11 | hours-per-week 1–99 |
| VAL-L1-12 | education-num ≥ 0 |
| VAL-L1-13 | Missing rate caps |
| VAL-L1-14 | No all-null features |
| VAL-L1-15 | No constant features |
| VAL-L1-16 | Categorical cardinality ≤ 100 |
| VAL-L1-17 | No duplicate feature rows |
| VAL-L1-18 | Stratified split reproducibility |

### Layer 2 — Smoke pipeline

| ID | Check |
|----|-------|
| VAL-L2-01 | ruff check + format |
| VAL-L2-02 | mypy |
| VAL-L2-03 | pytest unit |
| VAL-L2-04 | Dockerfile.train builds |
| VAL-L2-05 | import mlops |
| VAL-L2-06 | MLflow connectivity |
| VAL-L2-07 | Mini-train |
| VAL-L2-08 | Artifacts exist |
| VAL-L2-09 | Metrics finite |
| VAL-L2-10 | Smoke accuracy ≥ floor |
| VAL-L2-11 | Both classes predicted |
| VAL-L2-12 | MLflow params logged |
| VAL-L2-13 | Coverage ≥ threshold |

### Layer 3 — Run (`validate_run.py`)

| ID | Check |
|----|-------|
| VAL-L3-01 | Run FINISHED |
| VAL-L3-02 | Required metrics present |
| VAL-L3-03–05 | Metric floors |
| VAL-L3-06 | Overfit guard |
| VAL-L3-07 | Both classes on test |
| VAL-L3-08 | Positive rate band |
| VAL-L3-09 | Model loads |
| VAL-L3-10 | Metric reproducibility |
| VAL-L3-11 | Champion gate |
| VAL-L3-12 | Lineage params |
| VAL-L3-13 | No leakage |

### Layer 4 — Deploy

| ID | Check |
|----|-------|
| VAL-L4-01–12 | Docker build, compose, /health, /predict, schema, errors, latency |
| VAL-L4-13 | Pre-flight before production |

## decision_gates {#decision_gates}

1. VAL-L3 pass → register model `adult-income` version → alias `@staging`.
2. Deploy validates the exact Full Train artifact locally, then performs hosted L4 checks when HF configuration is available.
3. Only a verified candidate may be promoted to the `@production` alias by the protected manual path.

## iac_map {#iac_map}

| Resource | Terraform path |
|----------|----------------|
| HCP backend | `infra/terraform/backend.tf` |
| OIDC | `infra/terraform/oidc_github.tf` |
| S3 | `modules/storage` via `envs/showcase` |

## runbooks {#runbooks}

See [docs/CREDENTIALS.md](CREDENTIALS.md) and [infra/terraform/README.md](../infra/terraform/README.md).

## open_questions {#open_questions}

- ADR-002: DagsHub-only vs AWS S3 for artifacts (default: DagsHub).
- HF Space repository and runtime URL (set in `HF_SPACE_REPO` and `HF_SPACE_URL`).

## implementation_status {#implementation_status}

Implemented and enforced: data validation, lint/type/unit checks, smoke
training, Docker build/import, full-train run validation, champion comparison,
artifact hash/provenance checks, exact Smoke-CI prerequisite validation and
local serving verification. Hosted HF verification and production promotion
remain configuration-dependent; there is no confirmed hosted run or public
endpoint in this repository yet.

The validation catalogue above includes intended layer IDs for the complete
system. The executable checks in each workflow and script are the authority for
what is currently enforced.
