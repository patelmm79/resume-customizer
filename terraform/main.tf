terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
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
}

resource "google_artifact_registry_repository_iam_member" "repo_reader_run_agent" {
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-run.iam.gserviceaccount.com"
  depends_on = [null_resource.wait_for_run_runtime_sa, google_project_service.run_api, google_artifact_registry_repository.repo]
}

# NOTE: repository-level IAM binding for the Cloud Run runtime agent can fail
# if the Google-managed runtime service account doesn't yet exist. To avoid
# that race, grant the runtime agent the Artifact Registry reader role at
# the project level instead (accepted even if the SA is not yet present).
resource "google_project_iam_member" "run_agent_project_binding" {
  project = var.project
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-run.iam.gserviceaccount.com"
  depends_on = [google_project_service.artifact_api, google_project_service.run_api]
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
        image = var.image
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
    google_project_iam_member.run_agent_project_binding
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
