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
    google_project_service.artifact_api
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
