# Terraform configuration for Google Cloud Storage bucket for Resume Customizer settings
# This creates a GCS bucket for persisting .settings.json across deployments
# Only created when storage_provider = "gcs"
#
# Uses existing variables from main Cloud Run config:
# - project: GCP project ID
# - region: GCP region
# - service_name: Application name for resource naming

provider "google" {
  project = var.project
  region  = var.region
}

# GCS bucket for settings storage
resource "google_storage_bucket" "settings" {
  count         = var.storage_provider == "gcs" ? 1 : 0
  name          = "${var.service_name}-settings-${var.project}"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  labels = {
    app         = var.service_name
    environment = "production"
    purpose     = "settings-storage"
  }
}

# Block public access
resource "google_storage_bucket_iam_binding" "public_access" {
  count  = var.storage_provider == "gcs" ? 1 : 0
  bucket = google_storage_bucket.settings[0].name
  role   = "roles/storage.objectViewer"

  members = []  # No public access
}

# Service account for application access
resource "google_service_account" "app" {
  count        = var.storage_provider == "gcs" ? 1 : 0
  account_id   = "${var.service_name}-settings-sa"
  display_name = "Service account for Resume Customizer settings access"
}

# Grant permissions to service account
resource "google_storage_bucket_iam_member" "app_read_write" {
  count  = var.storage_provider == "gcs" ? 1 : 0
  bucket = google_storage_bucket.settings[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app[0].email}"
}

# Create service account key (for local testing/development)
# IMPORTANT: Store this securely! Don't commit to git.
# Uncomment only when needed for local development
# resource "google_service_account_key" "app" {
#   service_account_id = google_service_account.app.name
#   public_key_type    = "TYPE_X509_PEM_CERT"
# }

# Outputs (only populated if storage_provider = "gcs")
output "gcs_bucket_name" {
  description = "GCS bucket name for settings storage"
  value       = var.storage_provider == "gcs" ? google_storage_bucket.settings[0].name : null
}

output "gcs_bucket_region" {
  description = "GCS bucket region"
  value       = var.storage_provider == "gcs" ? var.region : null
}

output "gcs_service_account_email" {
  description = "Service account email for application"
  value       = var.storage_provider == "gcs" ? google_service_account.app[0].email : null
}

output "gcs_environment_vars" {
  description = "Environment variables to set for application (GCS)"
  value = var.storage_provider == "gcs" ? {
    RESUME_SETTINGS_STORAGE = "gcs"
    RESUME_SETTINGS_BUCKET  = google_storage_bucket.settings[0].name
    GOOGLE_CLOUD_PROJECT    = var.project
  } : null
}
