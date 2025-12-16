output "cloud_run_url" {
  description = "Cloud Run service URL (empty if not created)"
  value       = try(google_cloud_run_service.service[0].status[0].url, null)
}

output "service_account_email" {
  description = "Service account used by Cloud Run"
  value       = google_service_account.cloudrun_sa.email
}
