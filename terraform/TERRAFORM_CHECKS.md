# Terraform Configuration Checks

## Overview
This document summarizes all checks performed on the Terraform configuration to ensure reliability and prevent runtime failures with different variable combinations.

## Check Categories

### 1. **Conditional Resource References**
**What it checks**: Resources with `count` conditions are properly referenced with `[0]` notation or conditional logic.

**Why it matters**: When a resource has `count`, you can't reference it unconditionally. This causes "resource not found" errors.

**Examples**:
- ❌ Bad: `depends_on = [google_cloudbuild_trigger.repo_trigger]` when trigger has `count`
- ✅ Good: `depends_on = [..., (!condition) ? [google_cloudbuild_trigger.repo_trigger[0]] : []]`

**Checked resources**:
- `google_cloudbuild_trigger.repo_trigger` (count-based)
- `google_artifact_registry_repository_iam_member.repo_reader_sa` (count-based)
- `google_artifact_registry_repository_iam_member.repo_reader_default_sa` (count-based)
- `google_compute_default_service_account.default` (count-based)

---

### 2. **API Enablement Dependencies**
**What it checks**: All resources depending on a specific API are properly dependent on that API being enabled first.

**Why it matters**: Creating resources before their API is enabled causes "API not enabled" errors.

**Checked APIs**:
- **Secret Manager API**: Must be enabled before creating secrets
  - Resources: `google_secret_manager_secret.*`, `google_secret_manager_secret_version.*`
- **Cloud Build API**: Must be enabled before creating triggers/connections
  - Resources: `google_cloudbuildv2_connection`, `google_cloudbuild_trigger`
- **Cloud Run API**: Must be enabled before creating Cloud Run services
  - Resources: `google_cloud_run_service`, `google_cloud_run_service_iam_member`

---

### 3. **Condition Logic Consistency**
**What it checks**: When a resource has conditions controlling its creation, dependent resources must have compatible conditions.

**Why it matters**: Mismatched conditions cause resource references to fail when certain variables are set.

**Checked patterns**:
- `create_secrets=true` AND `create_secret_versions=true` (both must be true for versions)
- `create_github_connection=true` AND `github_token` provided (both must be true for connection)
- `use_default_sa=true` XOR `use_default_sa=false` (exactly one path)

---

### 4. **Cross-File Variable Consistency**
**What it checks**: All variables referenced in `.tf` files are defined in `variables.tf`.

**Why it matters**: Undefined variables cause terraform plan/apply to fail immediately.

**Checked**:
- All variable references in `main.tf`
- All variable references in `outputs.tf`
- Variable types match usage

---

### 5. **Data Source Dependencies**
**What it checks**: Data sources have explicit `depends_on` when they depend on resource creation.

**Why it matters**: Data sources can race with resource creation, causing intermittent failures.

**Checked data sources**:
- `data.google_compute_default_service_account.default` → depends on `google_project_service.run_api`

---

### 6. **Missing Required Fields**
**What it checks**: All resources have required fields populated (not left empty).

**Why it matters**: Missing required fields cause API validation errors.

**Checked fields**:
- `project` field on all Google resources
- `location` field on regional resources
- `secret_id` on secrets
- `replication` on secrets

---

### 7. **IAM Member Condition Handling**
**What it checks**: IAM bindings are properly gated with conditions when they reference conditional resources.

**Why it matters**: Granting IAM to resources that don't exist causes "resource not found" errors.

**Checked bindings**:
- GitHub token secret IAM (only when GitHub automation enabled)
- Default/custom service account IAM (conditional on `use_default_sa`)

---

## Test Scenarios

These variable combinations are tested to ensure no failures:

| Scenario | Variables | Expected Resources |
|----------|-----------|-------------------|
| Manual GitHub | `create_github_connection=false` | Trigger created, no connection |
| Auto GitHub | `create_github_connection=true, github_token=<value>` | Connection created, no trigger |
| Secrets Only | `create_secrets=true, create_secret_versions=false` | Secrets created, no versions |
| Secrets + Versions | `create_secrets=true, create_secret_versions=true` | Secrets AND versions created |
| Default SA | `use_default_sa=true` | Default SA used, custom SA not created |
| Custom SA | `use_default_sa=false` | Custom SA created, default SA not used |

---

## Summary of Fixes Applied

### Critical Issues Fixed (8 total)

| # | Issue | Severity | Fix Applied |
|---|-------|----------|-------------|
| 1 | Cloud Run unconditional depends_on for conditional resources | HIGH | Use `concat()` with conditional logic |
| 2 | Secret Manager API only enabled for GitHub | HIGH | Always enable Secret Manager API |
| 3 | Secret versions created without checking create_secrets | HIGH | Add `create_secrets &&` to condition |
| 4 | Unconditional IAM member references | HIGH | Make IAM depends_on conditional |
| 5 | Data source missing explicit depends_on | MEDIUM | Add `depends_on = [run_api]` |
| 6 | Secrets missing `depends_on` for API | MEDIUM | Add `depends_on = [secretmanager_api]` |
| 7 | Missing `project` field on resources | MEDIUM | Add `project = var.project` |
| 8 | Circular/missing dependencies | MEDIUM | Explicit depends_on added throughout |

---

## Running Manual Checks

### Pre-apply Checklist

```bash
# 1. Validate Terraform syntax
terraform validate

# 2. Format check
terraform fmt -check -recursive .

# 3. Plan and review
terraform plan -out=tfplan

# 4. Review planned changes
terraform show tfplan

# 5. Apply (once approved)
terraform apply tfplan
```

### Test Variable Combinations

```bash
# Test 1: Manual GitHub setup
terraform plan -var="create_github_connection=false"

# Test 2: Automated GitHub
terraform plan -var="create_github_connection=true" -var="github_token=ghp_..."

# Test 3: Default Service Account
terraform plan -var="use_default_sa=true"

# Test 4: Custom Service Account
terraform plan -var="use_default_sa=false"

# Test 5: With secrets but no versions
terraform plan -var="create_secrets=true" -var="create_secret_versions=false"

# Test 6: With secrets and versions
terraform plan -var="create_secrets=true" -var="create_secret_versions=true" \
  -var="gemini_api_key_value=test" \
  -var="anthropic_api_key_value=test" \
  -var="custom_llm_api_key_value=test"
```

---

## Automated Validation Tools

See `validate_terraform.sh` and `validate_terraform.py` for automated checks.
