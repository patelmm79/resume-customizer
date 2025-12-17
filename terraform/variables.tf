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

variable "llm_provider" {
  description = "Default LLM provider (gemini, claude, custom)"
  type        = string
  default     = ""
}

variable "gemini_model" {
  description = "Default Gemini model name"
  type        = string
  default     = "gemini-2.0-flash-exp"
}

variable "claude_model" {
  description = "Default Claude model name"
  type        = string
  default     = "claude-3-5-sonnet-20241022"
}

variable "custom_llm_base_url" {
  description = "Base URL for a custom OpenAI-compatible LLM"
  type        = string
  default     = ""
}

variable "custom_llm_model" {
  description = "Default model name for custom LLMs"
  type        = string
  default     = ""
}

variable "custom_llm_max_retries" {
  description = "Max retry attempts for custom LLM (503/backoff)"
  type        = number
  default     = 5
}

variable "custom_llm_initial_retry_delay" {
  description = "Initial retry delay (seconds) for custom LLM backoff"
  type        = number
  default     = 5.0
}

variable "custom_llm_context_limit" {
  description = "Estimated context limit (tokens) for custom LLMs"
  type        = number
  default     = 32768
}

variable "secret_prefix" {
  description = "Prefix to use when creating Secret Manager secret names for this application (avoids collisions)"
  type        = string
  default     = "resume_customizer"
}

# Whether Terraform should create Secret Manager secret resources (values should be populated by CI)
variable "create_secrets" {
  description = "If true, Terraform will create Secret Manager secret resources for standard keys. Secret values should be added as versions by CI or other tools."
  type        = bool
  default     = true
}



