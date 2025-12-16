variable "project" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "resume-customizer"
}

variable "artifact_repo" {
  description = "Artifact Registry repository id"
  type        = string
  default     = "resume-customizer-repo"
}

variable "image" {
  description = "Container image URL (Artifact Registry or GCR). If empty, uses default path based on project/region/artifact_repo"
  type        = string
  default     = ""
}

variable "port" {
  description = "Container port Streamlit listens on"
  type        = number
  default     = 8080
}

# GitHub trigger variables for Cloud Build
variable "github_owner" {
  description = "GitHub owner (user or org) where the repo lives"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_branch" {
  description = "Branch to trigger builds from"
  type        = string
  default     = "main"
}

variable "create_runtime_bindings" {
  description = "When false, skip creating IAM bindings for the Google-managed Cloud Run runtime service account (useful for first apply).\nSet to true on the second apply after the runtime service account exists."
  type        = bool
  default     = false
}

variable "use_default_sa" {
  description = "If true, use the default Compute Engine service account instead of creating a custom one"
  type        = bool
  default     = false
}


