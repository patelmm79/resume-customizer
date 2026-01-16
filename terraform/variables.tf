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

# Optional: let Terraform create secret versions when values are provided via TF_VAR or CI
variable "create_secret_versions" {
  description = "When true, Terraform will create secret versions for the standard keys when corresponding values are provided. Set to false to manage versions outside Terraform."
  type        = bool
  default     = true
}

variable "gemini_api_key_value" {
  description = "Optional: GEMINI API key value to add as a secret version (set via TF_VAR or CI)."
  type        = string
  default     = ""
}

variable "anthropic_api_key_value" {
  description = "Optional: ANTHROPIC API key value to add as a secret version (set via TF_VAR or CI)."
  type        = string
  default     = ""
}

variable "custom_llm_api_key_value" {
  description = "Optional: CUSTOM LLM API key value to add as a secret version (set via TF_VAR or CI)."
  type        = string
  default     = ""
}

# GitHub connection variables for Cloud Build (optional automation)
variable "github_token" {
  description = "Optional: GitHub Personal Access Token to automate GitHub connection setup. If provided, Terraform will create the GitHub connection. If empty, you must manually create the connection in Cloud Console."
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_github_connection" {
  description = "If true and github_token is provided, Terraform will create the GitHub Cloud Build connection. Set to false to use manual connection setup."
  type        = bool
  default     = false
}

# Environment identifier for multi-instance deployments
variable "environment" {
  description = "Environment name (dev, staging, prod, etc.). Used for workspace naming and resource organization in cloud deployments."
  type        = string
  default     = "dev"
}

# LangSmith integration variables
variable "langsmith_tracing" {
  description = "LangSmith tracing setting (true to enable)"
  type        = bool
  default     = false
}

variable "langsmith_endpoint" {
  description = "LangSmith API endpoint URL (e.g., https://api.smith.langchain.com)"
  type        = string
  default     = ""
}

variable "langsmith_api_key_value" {
  description = "Optional: LangSmith API key value to add as a secret version. Can be provided via terraform.tfvars, TF_VAR environment variable, or CI. Will be stored in Secret Manager and mounted as LANGSMITH_API_KEY environment variable in Cloud Run."
  type        = string
  default     = ""
  sensitive   = true
}

variable "langfuse_enabled" {
  description = "Enable Langfuse tracing (true to enable)"
  type        = bool
  default     = false
}

variable "langfuse_host" {
  description = "Langfuse host URL (e.g., https://cloud.langfuse.com or self-hosted URL)"
  type        = string
  default     = "https://cloud.langfuse.com"
}

variable "langfuse_public_key_value" {
  description = "Optional: Langfuse public key value to add as a secret version. Can be provided via terraform.tfvars, TF_VAR environment variable, or CI. Will be stored in Secret Manager and mounted as LANGFUSE_PUBLIC_KEY environment variable in Cloud Run."
  type        = string
  default     = ""
  sensitive   = true
}

variable "langfuse_secret_key_value" {
  description = "Optional: Langfuse secret key value to add as a secret version. Can be provided via terraform.tfvars, TF_VAR environment variable, or CI. Will be stored in Secret Manager and mounted as LANGFUSE_SECRET_KEY environment variable in Cloud Run."
  type        = string
  default     = ""
  sensitive   = true
}

