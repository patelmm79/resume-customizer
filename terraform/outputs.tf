output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_account_email" {
  description = "Service account used by Cloud Run"
  value       = var.use_default_sa ? data.google_compute_default_service_account.default[0].email : google_service_account.cloudrun_sa[0].email
}

output "github_connection_created" {
  description = "Whether GitHub connection was created via automation"
  value       = var.create_github_connection && length(trimspace(var.github_token)) > 0
}

output "next_steps" {
  description = "Next steps after Terraform apply"
  value = var.create_github_connection && length(trimspace(var.github_token)) > 0 ?
    "GitHub v2 connection created! Now manually create the Cloud Build trigger:\n1. Go to: https://console.cloud.google.com/cloud-build/triggers\n2. Click 'Create Trigger'\n3. Name: 'resume-customizer'\n4. Event: Push to a branch\n5. Repository: ${var.github_owner}/${var.github_repo}\n6. Branch: ^${var.github_branch}$\n7. Build configuration: cloudbuild.yaml\n8. Click Create" :
    "To create a trigger, provide github_token and set create_github_connection=true"
}
