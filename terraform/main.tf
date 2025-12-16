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
      gcloud builds submit --config=cloudbuild.yaml --substitutions=_IMAGE="$IMAGE",_SERVICE_NAME=${var.service_name},_REGION=${var.region} --project=${var.project}
    EOT
    interpreter = ["/bin/sh","-c"]
  }

  depends_on = [google_project_service.cloudbuild_api, google_project_service.artifact_api]
  
}

# Ensure Cloud Run service account and Cloud Run runtime have read access to the repo
data "google_project" "project" {
  project_id = var.project
}

# Wait for Cloud Run runtime service account to be created (helps prevent race conditions)
resource "null_resource" "wait_for_run_runtime_sa" {
  provisioner "local-exec" {
    command = <<EOT
#!/bin/sh
set -e
PROJECT="${var.project}"
PN=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
SA="service-$${PN}@gcp-sa-run.iam.gserviceaccount.com"
echo "Waiting for Cloud Run runtime service account: $${SA}"
COUNT=0
while [ $COUNT -lt 60 ]; do
  if gcloud iam service-accounts describe "$SA" --project="$PROJECT" >/dev/null 2>&1; then
    echo "Found $${SA}"
    exit 0
  fi
  COUNT=$((COUNT+1))
  sleep 5
done
echo "Timed out waiting for $${SA}; proceeding and hope it is created later"
exit 0
EOT
    interpreter = ["/bin/sh", "-c"]
  }
}

resource "google_artifact_registry_repository_iam_member" "repo_reader_sa" {
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloudrun_sa.email}"
  depends_on = [
    google_artifact_registry_repository.repo,
    google_service_account.cloudrun_sa,
    google_project_service.artifact_api
  ]
}


# Robust binding: wait for Google-managed Cloud Run runtime SA, then
# add Artifact Registry reader role using `gcloud` so we avoid API race
# conditions that cause Terraform to fail when the SA is not yet present.
resource "null_resource" "run_agent_bindings" {
  count = var.create_runtime_bindings ? 1 : 0

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      PROJECT=${var.project}
      REGION=${var.region}
      REPO=${google_artifact_registry_repository.repo.repository_id}

      PN=$(gcloud projects describe "$${PROJECT}" --format='value(projectNumber)')
      SA="service-$${PN}@gcp-sa-run.iam.gserviceaccount.com"

      echo "Waiting for Cloud Run runtime service account: $${SA}"
      COUNT=0
      until gcloud iam service-accounts describe "$${SA}" --project="$${PROJECT}" >/dev/null 2>&1; do
        COUNT=$((COUNT+1))
        if [ $COUNT -gt 60 ]; then
          echo "Timed out waiting for $${SA}"
          exit 1
        fi
        sleep 5
      done

      echo "Adding project-level Artifact Registry read role for $${SA}"
      gcloud projects add-iam-policy-binding "$${PROJECT}" \
        --member="serviceAccount:$${SA}" \
        --role="roles/artifactregistry.reader"

      echo "Adding repository-level Artifact Registry read role for $${SA}"
      gcloud artifacts repositories add-iam-policy-binding "$${REPO}" \
        --project="$${PROJECT}" \
        --location="$${REGION}" \
        --member="serviceAccount:$${SA}" \
        --role="roles/artifactregistry.reader" || true

      echo "Done: $${SA} should have Artifact Registry reader access."
    EOT
    interpreter = ["/bin/sh", "-c"]
  }

  depends_on = [google_artifact_registry_repository.repo, null_resource.wait_for_run_runtime_sa, google_project_service.artifact_api, google_project_service.run_api]
}

# Service account for Cloud Run (optional - can use default)
resource "google_service_account" "cloudrun_sa" {
  account_id   = "resume-customizer-sa"
  display_name = "Service account for Resume Customizer Cloud Run"
}

# Cloud Run service (managed)
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloudrun_sa.email
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
    google_artifact_registry_repository_iam_member.repo_reader_sa
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
