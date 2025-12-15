output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_account_email" {
  description = "Service account used by Cloud Run"
  value       = google_service_account.cloudrun_sa.email
}
