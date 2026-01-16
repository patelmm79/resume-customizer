terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

# Beta provider for resources not present in the stable provider


# Compute final image if not provided explicitly
locals {
  image = length(trimspace(var.image)) > 0 ? var.image : "${var.region}-docker.pkg.dev/${var.project}/${var.artifact_repo}/resume-customizer:latest"
}

# Enable required APIs
resource "google_project_service" "run_api" {
  project = var.project
  service = "run.googleapis.com"
}

resource "google_project_service" "cloudbuild_api" {
  project = var.project
  service = "cloudbuild.googleapis.com"
}

resource "google_project_service" "artifact_api" {
  project = var.project
  service = "artifactregistry.googleapis.com"
}

# Wait for API to be fully enabled before creating repository
# (API enablement needs time to propagate to Google's systems)
resource "time_sleep" "artifact_api_propagation" {
  depends_on = [google_project_service.artifact_api]

  create_duration  = "15s"
  destroy_duration = "0s"
}

# Artifact Registry repository for container images
resource "google_artifact_registry_repository" "repo" {
  provider = google
  project  = var.project
  location = var.region
  repository_id = var.artifact_repo
  format = "DOCKER"
  description = "Repository for resume-customizer images"

  depends_on = [time_sleep.artifact_api_propagation]
}

# Build and push Docker image to Artifact Registry using Cloud Build
resource "null_resource" "docker_build" {
  triggers = {
    dockerfile_hash  = filesha256("${path.module}/../Dockerfile")
    requirements_hash = filesha256("${path.module}/../requirements.txt")
    app_hash = filesha256("${path.module}/../app.py")
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      cd "${path.module}/.."
      IMAGE=${var.region}-docker.pkg.dev/${var.project}/${var.artifact_repo}/resume-customizer:latest

      echo "Building and pushing image: $IMAGE"
      gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_IMAGE="$IMAGE",_SERVICE_NAME=${var.service_name},_REGION=${var.region} \
        --project=${var.project}

      echo "Build complete. Image should be available at: $IMAGE"
    EOT
    interpreter = ["/bin/sh","-c"]
  }

  depends_on = [
    google_project_service.cloudbuild_api,
    google_project_service.artifact_api,
    google_artifact_registry_repository.repo
  ]

}

# Enable Secret Manager API (needed for GitHub token and LLM API key storage)
resource "google_project_service" "secretmanager_api" {
  project = var.project
  service = "secretmanager.googleapis.com"
}

# Store GitHub token in Secret Manager if provided
resource "google_secret_manager_secret" "github_token" {
  count     = var.create_github_connection && length(trimspace(var.github_token)) > 0 ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-GITHUB_TOKEN"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "github_token" {
  count       = var.create_github_connection && length(trimspace(var.github_token)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.github_token[0].id
  secret_data = var.github_token
}

# Grant Cloud Build service account access to GitHub token secret
resource "google_secret_manager_secret_iam_member" "github_token_accessor" {
  count     = var.create_github_connection && length(trimspace(var.github_token)) > 0 ? 1 : 0
  secret_id = google_secret_manager_secret.github_token[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
  depends_on = [
    google_secret_manager_secret.github_token
  ]
}

# Create GitHub connection using token (v2 API)
resource "google_cloudbuildv2_connection" "github" {
  count           = var.create_github_connection && length(trimspace(var.github_token)) > 0 ? 1 : 0
  project         = var.project
  location        = var.region
  name            = "github-connection"
  disabled        = false

  github_config {
    authorizer_credential {
      oauth_token_secret_version = google_secret_manager_secret_version.github_token[0].id
    }
  }

  depends_on = [
    google_project_service.cloudbuild_api,
    google_secret_manager_secret_version.github_token,
    google_secret_manager_secret_iam_member.github_token_accessor
  ]
}

# Create an in-cloud Cloud Build build (uses beta provider resource)
/* Use Cloud Build Trigger instead of direct Build resource (trigger runs on push).
   The trigger will run Cloud Build using `cloudbuild.yaml` in the repository.
   This works with the stable provider and supports remote Terraform runs.
*/
# V1 Trigger for manual GitHub connection setup
resource "google_cloudbuild_trigger" "repo_trigger" {
  count    = !var.create_github_connection || length(trimspace(var.github_token)) == 0 ? 1 : 0

  project  = var.project
  location = var.region
  filename = "cloudbuild.yaml"

  github {
    owner = var.github_owner
    name  = var.github_repo

    push {
      branch = var.github_branch
    }
  }

  substitutions = {
    _REGION       = var.region
    _SERVICE_NAME = var.service_name
    _IMAGE        = local.image
  }

  description = "Build and deploy resume-customizer on push to ${var.github_branch}"
  disabled    = false

  depends_on = [
    google_project_service.cloudbuild_api
  ]
}

# NOTE: When using v2 connection (created above with GitHub token), the v1 trigger
# automatically uses the v2 connection. The trigger above will work seamlessly with
# the v2 connection once it's created. No separate v2 trigger resource is needed.
#
# The google_cloudbuild_trigger resource will automatically:
# 1. Use the v2 connection when it exists (via the GitHub App)
# 2. Enable automatic builds on push to the specified branch
# 3. Run the cloudbuild.yaml pipeline automatically
#
# For full details on how v1 triggers work with v2 connections, see:
# https://cloud.google.com/build/docs/trigger-v2-connection

# Project data for reference
data "google_project" "project" {
  project_id = var.project
}

resource "google_artifact_registry_repository_iam_member" "repo_reader_sa" {
  count      = var.use_default_sa ? 0 : 1
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloudrun_sa[0].email}"
  depends_on = [
    google_artifact_registry_repository.repo,
    google_service_account.cloudrun_sa,
    google_project_service.artifact_api
  ]
}

# Ensure Cloud Build service account can write to Artifact Registry when builds run in-cloud
resource "google_artifact_registry_repository_iam_member" "repo_writer_cloudbuild" {
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
  depends_on = [google_artifact_registry_repository.repo]
}

# Grant Cloud Build service account permission to push to Artifact Registry


# Grant default service account Artifact Registry access if using it
resource "google_artifact_registry_repository_iam_member" "repo_reader_default_sa" {
  count      = var.use_default_sa ? 1 : 0
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_compute_default_service_account.default[0].email}"
  depends_on = [
    google_artifact_registry_repository.repo,
    google_project_service.artifact_api
  ]
}

# Use gcloud to ensure custom SA has artifact registry permissions
# (more robust than relying solely on Terraform IAM binding)
# Only runs if not using default SA
resource "null_resource" "custom_sa_artifact_binding" {
  count = var.use_default_sa ? 0 : 1

  provisioner "local-exec" {
    command = <<-EOT
      PROJECT=${var.project}
      REGION=${var.region}
      REPO=${google_artifact_registry_repository.repo.repository_id}
      SA_EMAIL=${google_service_account.cloudrun_sa[0].email}

      echo "================================================"
      echo "Granting Artifact Registry permissions to: $${SA_EMAIL}"
      echo "Repository: $${REPO}"
      echo "Project: $${PROJECT}"
      echo "================================================"

      # Project-level binding
      echo "1. Adding project-level Artifact Registry reader role..."
      if gcloud projects add-iam-policy-binding "$${PROJECT}" \
        --member="serviceAccount:$${SA_EMAIL}" \
        --role="roles/artifactregistry.reader" \
        --condition=None \
        --quiet 2>&1; then
        echo "   ✓ Project-level binding succeeded"
      else
        echo "   ⚠ Project-level binding may have failed or role already assigned"
      fi

      # Repository-level binding
      echo "2. Adding repository-level Artifact Registry reader role..."
      if gcloud artifacts repositories add-iam-policy-binding "$${REPO}" \
        --project="$${PROJECT}" \
        --location="$${REGION}" \
        --member="serviceAccount:$${SA_EMAIL}" \
        --role="roles/artifactregistry.reader" \
        --quiet 2>&1; then
        echo "   ✓ Repository-level binding succeeded"
      else
        echo "   ⚠ Repository-level binding may have failed or role already assigned"
      fi

      # Wait for IAM propagation (increased from 3 to 10 seconds)
      echo "3. Waiting 10 seconds for IAM propagation..."
      sleep 10

      # Verify permissions
      echo "4. Verifying permissions..."
      if gcloud artifacts repositories get-iam-policy "$${REPO}" \
        --project="$${PROJECT}" \
        --location="$${REGION}" \
        --format="value(bindings[].members[])" 2>/dev/null | grep -q "$${SA_EMAIL}"; then
        echo "   ✓ Verified: Service account has Artifact Registry access"
      else
        echo "   ⚠ Warning: Could not verify service account permissions"
      fi

      echo "================================================"
      echo "IAM binding process complete"
      echo "================================================"
    EOT
    interpreter = ["/bin/sh", "-c"]
  }

  depends_on = [
    google_artifact_registry_repository.repo,
    google_service_account.cloudrun_sa,
    google_project_service.artifact_api,
    google_artifact_registry_repository_iam_member.repo_reader_sa
  ]
}


# Robust binding: wait for Google-managed Cloud Run runtime SA, then
# add Artifact Registry reader role using `gcloud` so we avoid API race
# conditions that cause Terraform to fail when the SA is not yet present.
# This is OPTIONAL and runs only after Cloud Run service is created (when create_runtime_bindings=true)
resource "null_resource" "run_agent_bindings" {
  count = var.create_runtime_bindings ? 1 : 0

  provisioner "local-exec" {
    command = <<-EOT
      PROJECT=${var.project}
      REGION=${var.region}
      REPO=${google_artifact_registry_repository.repo.repository_id}

      PN=$(gcloud projects describe "$${PROJECT}" --format='value(projectNumber)')
      SA="service-$${PN}@gcp-sa-run.iam.gserviceaccount.com"

      echo "================================================"
      echo "Setting up Google-managed Cloud Run runtime SA permissions"
      echo "Service Account: $${SA}"
      echo "================================================"

      echo "Waiting for Cloud Run runtime service account to be created..."
      COUNT=0
      while [ $COUNT -lt 120 ]; do
        if gcloud iam service-accounts describe "$${SA}" --project="$${PROJECT}" >/dev/null 2>&1; then
          echo "✓ Service account found: $${SA}"
          break
        fi
        COUNT=$((COUNT+1))
        if [ $COUNT -eq 120 ]; then
          echo "⚠ Timed out waiting for service account (after 10 minutes)"
          echo "This is OK - the service account may be created later"
          echo "You can rerun: terraform apply -var='create_runtime_bindings=true'"
          exit 0
        fi
        sleep 5
      done

      echo "Adding Artifact Registry reader role to $${SA}..."
      if gcloud projects add-iam-policy-binding "$${PROJECT}" \
        --member="serviceAccount:$${SA}" \
        --role="roles/artifactregistry.reader" \
        --quiet 2>&1 >/dev/null; then
        echo "✓ Project-level binding succeeded"
      else
        echo "⚠ Project-level binding may have failed or role already assigned"
      fi

      if gcloud artifacts repositories add-iam-policy-binding "$${REPO}" \
        --project="$${PROJECT}" \
        --location="$${REGION}" \
        --member="serviceAccount:$${SA}" \
        --role="roles/artifactregistry.reader" \
        --quiet 2>&1 >/dev/null; then
        echo "✓ Repository-level binding succeeded"
      else
        echo "⚠ Repository-level binding may have failed or role already assigned"
      fi

      echo "================================================"
      echo "Done: $${SA} should have Artifact Registry access"
      echo "================================================"
    EOT
    interpreter = ["/bin/sh", "-c"]
  }

  depends_on = [
    google_cloud_run_service.service,
    google_artifact_registry_repository.repo,
    google_project_service.artifact_api,
    google_project_service.run_api
  ]
}

# Service account for Cloud Run (optional - can use default)
resource "google_service_account" "cloudrun_sa" {
  count        = var.use_default_sa ? 0 : 1
  account_id   = "resume-customizer-sa"
  display_name = "Service account for Resume Customizer Cloud Run"
}

# Secret Manager: create standard secret resources for this app (no secret versions)
resource "google_secret_manager_secret" "gemini_api_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-GEMINI_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-ANTHROPIC_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret" "custom_llm_api_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-CUSTOM_LLM_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret" "langsmith_api_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-LANGSMITH_API_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret" "langfuse_public_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-LANGFUSE_PUBLIC_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret" "langfuse_secret_key" {
  count     = var.create_secrets ? 1 : 0
  project   = var.project
  secret_id = "${var.secret_prefix}-LANGFUSE_SECRET_KEY"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

# Optionally create secret versions when values are provided via variables/CI
# Note: requires both create_secrets AND create_secret_versions to be true
resource "google_secret_manager_secret_version" "gemini_api_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.gemini_api_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.gemini_api_key[0].id
  secret_data = var.gemini_api_key_value
}

resource "google_secret_manager_secret_version" "anthropic_api_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.anthropic_api_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.anthropic_api_key[0].id
  secret_data = var.anthropic_api_key_value
}

resource "google_secret_manager_secret_version" "custom_llm_api_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.custom_llm_api_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.custom_llm_api_key[0].id
  secret_data = var.custom_llm_api_key_value
}

resource "google_secret_manager_secret_version" "langsmith_api_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.langsmith_api_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.langsmith_api_key[0].id
  secret_data = var.langsmith_api_key_value
}

resource "google_secret_manager_secret_version" "langfuse_public_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.langfuse_public_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.langfuse_public_key[0].id
  secret_data = var.langfuse_public_key_value
}

resource "google_secret_manager_secret_version" "langfuse_secret_key_version" {
  count       = var.create_secrets && var.create_secret_versions && length(trimspace(var.langfuse_secret_key_value)) > 0 ? 1 : 0
  secret      = google_secret_manager_secret.langfuse_secret_key[0].id
  secret_data = var.langfuse_secret_key_value
}

# Fail fast: if `create_secret_versions` is true, require all three secret value variables
# to be provided (this enforces that values come from terraform.tfvars/TF_VARs).
/* Validation of required TF_VARs is implemented via variable validation blocks in variables.tf */

# External check: run a small script during plan to fail with a clear message
# if create_secret_versions = true but required TF_VAR secret values are missing.
data "external" "require_secret_values" {
  program = ["python", "${path.module}/validate_secret_vars.py"]
  query = {
    create_secret_versions = var.create_secret_versions
    gemini                  = var.gemini_api_key_value
    anthropic               = var.anthropic_api_key_value
    custom                  = var.custom_llm_api_key_value
  }
}

# Grant Cloud Run service account access to secrets
locals {
  cloudrun_sa_email = var.use_default_sa ? data.google_compute_default_service_account.default[0].email : google_service_account.cloudrun_sa[0].email
}

resource "google_secret_manager_secret_iam_member" "gemini_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.gemini_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "anthropic_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.anthropic_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "custom_llm_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.custom_llm_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "langsmith_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.langsmith_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "langfuse_public_key_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.langfuse_public_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "langfuse_secret_key_accessor" {
  count     = var.create_secrets ? 1 : 0
  secret_id = google_secret_manager_secret.langfuse_secret_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloudrun_sa_email}"
}

# Get the default Compute Engine service account
data "google_compute_default_service_account" "default" {
  count   = var.use_default_sa ? 1 : 0
  project = var.project
  depends_on = [google_project_service.run_api]
}

# Cloud Run service (managed)
# Uses either custom service account (cloudrun_sa) or default Compute Engine SA based on use_default_sa
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = var.use_default_sa ? data.google_compute_default_service_account.default[0].email : google_service_account.cloudrun_sa[0].email
      containers {
        image = local.image
        ports {
          container_port = var.port
        }
          # Non-secret runtime config
          env {
            name  = "LLM_PROVIDER"
            value = var.llm_provider
          }
          env {
            name  = "GEMINI_MODEL"
            value = var.gemini_model
          }
          env {
            name  = "CLAUDE_MODEL"
            value = var.claude_model
          }
          env {
            name  = "CUSTOM_LLM_BASE_URL"
            value = var.custom_llm_base_url
          }
          env {
            name  = "CUSTOM_LLM_MODEL"
            value = var.custom_llm_model
          }
          env {
            name  = "CUSTOM_LLM_MAX_RETRIES"
            value = tostring(var.custom_llm_max_retries)
          }
          env {
            name  = "CUSTOM_LLM_INITIAL_RETRY_DELAY"
            value = tostring(var.custom_llm_initial_retry_delay)
          }
          env {
            name  = "CUSTOM_LLM_CONTEXT_LIMIT"
            value = tostring(var.custom_llm_context_limit)
          }

          # LangSmith integration
          env {
            name  = "LANGSMITH_PROJECT"
            value = var.service_name
          }
          env {
            name  = "LANGSMITH_TRACING"
            value = tostring(var.langsmith_tracing)
          }
          env {
            name  = "LANGSMITH_ENDPOINT"
            value = var.langsmith_endpoint
          }

          # Langfuse integration
          env {
            name  = "LANGFUSE_ENABLED"
            value = tostring(var.langfuse_enabled)
          }
          env {
            name  = "LANGFUSE_HOST"
            value = var.langfuse_host
          }

          # Secret-mounted env vars (map to Secret Manager secrets created above)
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "GEMINI_API_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.gemini_api_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "ANTHROPIC_API_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.anthropic_api_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "CUSTOM_LLM_API_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.custom_llm_api_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "LANGSMITH_API_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.langsmith_api_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "LANGFUSE_PUBLIC_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.langfuse_public_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
          dynamic "env" {
            for_each = var.create_secrets ? [1] : []
            content {
              name = "LANGFUSE_SECRET_KEY"
              value_from {
                secret_key_ref {
                  name = google_secret_manager_secret.langfuse_secret_key[0].secret_id
                  key  = "latest"
                }
              }
            }
          }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  # Note: Terraform depends_on requires static lists, so we use conditional resources to manage dependencies
  # The following implicit dependencies are created through resource references:
  # - Artifact Registry IAM members (conditionally referenced via local.cloudrun_sa_email)
  # - Cloud Build trigger (has count condition, will be implicit if created)
  # Explicit static dependencies:
  depends_on = [
    google_project_service.run_api,
    google_project_service.artifact_api,
    google_secret_manager_secret_iam_member.gemini_accessor,
    google_secret_manager_secret_iam_member.anthropic_accessor,
    google_secret_manager_secret_iam_member.custom_llm_accessor,
    google_secret_manager_secret_iam_member.langsmith_accessor,
    google_secret_manager_secret_iam_member.langfuse_public_key_accessor,
    google_secret_manager_secret_iam_member.langfuse_secret_key_accessor
  ]
}

# Allow unauthenticated invocations (public)
resource "google_cloud_run_service_iam_member" "invoker" {
  location = google_cloud_run_service.service.location
  project  = var.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
