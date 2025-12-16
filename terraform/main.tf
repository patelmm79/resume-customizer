terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

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

# Artifact Registry repository for container images
resource "google_artifact_registry_repository" "repo" {
  provider = google
  project  = var.project
  location = var.region
  repository_id = var.artifact_repo
  format = "DOCKER"
  description = "Repository for resume-customizer images"
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

  depends_on = [google_project_service.cloudbuild_api, google_project_service.artifact_api]

}

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

# Get the default Compute Engine service account
data "google_compute_default_service_account" "default" {
  count   = var.use_default_sa ? 1 : 0
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
        env {
          name  = "PORT"
          value = tostring(var.port)
        }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.run_api,
    google_project_service.artifact_api,
    null_resource.docker_build,
    google_artifact_registry_repository_iam_member.repo_reader_sa,
    google_artifact_registry_repository_iam_member.repo_reader_default_sa
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
