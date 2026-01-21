# Terraform configuration for Google Cloud Storage bucket for Resume Customizer settings
# This creates a GCS bucket for persisting .settings.json across deployments

# NOTE: This file is an alternative to settings-s3.tf
# Use this if deploying to Google Cloud Platform instead of AWS

# Set GCP project
variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

# Set application name
variable "app_name" {
  description = "Application name (used in resource naming)"
  default     = "resume-customizer"
}

provider "google" {
  project = var.gcp_project
  region  = var.region
}

# GCS bucket for settings storage
resource "google_storage_bucket" "settings" {
  name          = "${var.app_name}-settings-${var.gcp_project}"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  labels = {
    app         = var.app_name
    environment = "production"
    purpose     = "settings-storage"
  }
}

# Block public access
resource "google_storage_bucket_iam_binding" "public_access" {
  bucket = google_storage_bucket.settings.name
  role   = "roles/storage.objectViewer"

  members = []  # No public access
}

# Service account for application access
resource "google_service_account" "app" {
  account_id   = "${var.app_name}-settings-sa"
  display_name = "Service account for Resume Customizer settings access"
}

# Grant permissions to service account
resource "google_storage_bucket_iam_member" "app_read_write" {
  bucket = google_storage_bucket.settings.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app.email}"
}

# Create service account key (for local testing/development)
# IMPORTANT: Store this securely! Don't commit to git.
# Uncomment only when needed for local development
# resource "google_service_account_key" "app" {
#   service_account_id = google_service_account.app.name
#   public_key_type    = "TYPE_X509_PEM_CERT"
# }

# Outputs
output "bucket_name" {
  description = "GCS bucket name for settings storage"
  value       = google_storage_bucket.settings.name
}

output "bucket_region" {
  description = "GCS bucket region"
  value       = var.region
}

output "service_account_email" {
  description = "Service account email for application"
  value       = google_service_account.app.email
}

output "environment_vars" {
  description = "Environment variables to set for application"
  value = {
    RESUME_SETTINGS_STORAGE = "gcs"
    RESUME_SETTINGS_BUCKET  = google_storage_bucket.settings.name
    GOOGLE_CLOUD_PROJECT    = var.gcp_project
  }
}
