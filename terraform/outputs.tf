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
  sensitive   = true  # Sensitive because it references var.github_token
}

output "next_steps" {
  description = "Next steps after Terraform apply"
  value = var.create_github_connection && length(trimspace(var.github_token)) > 0 ? join("", [
    "✅ GitHub connection and Cloud Build trigger created automatically!\n\n",
    "CI/CD is now fully automated:\n",
    "• The GitHub v2 connection authenticates with your repository\n",
    "• The Cloud Build trigger monitors your repository for commits\n",
    "• Every push to branch '${var.github_branch}' triggers a build\n",
    "• Your cloudbuild.yaml pipeline will run automatically\n\n",
    "Next steps:\n",
    "1. Push a commit to ${var.github_repo} branch ${var.github_branch}\n",
    "2. Watch the build progress: https://console.cloud.google.com/cloud-build/builds\n",
    "3. Once the image is built and pushed, verify at: https://console.cloud.google.com/artifacts\n",
    "4. Cloud Run will be updated if your cloudbuild.yaml includes deployment steps\n",
    "5. Access your app at: ${google_cloud_run_service.service.status[0].url}"
  ]) : "Configure github_token and set create_github_connection=true to enable fully automatic CI/CD"
  sensitive = true  # Sensitive because it references var.github_token
}
