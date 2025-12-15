resource "google_cloudbuild_trigger" "github_trigger" {
  project  = var.project
  name     = "${var.service_name}-github-trigger"
  filename = "cloudbuild.yaml"

  github {
    owner           = var.github_owner
    name            = var.github_repo
    installation_id = var.github_installation_id

    push {
      branch = var.github_branch
    }
  }

  included_files = ["**"]
}
