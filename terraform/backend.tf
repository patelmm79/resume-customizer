# Terraform Backend Configuration
# This file configures where Terraform stores its state.
#
# For multi-instance deployments, use ONE of the following approaches:
#
# APPROACH 1: Terraform Cloud (Recommended for cloud deployments)
# - Supports workspaces for environment isolation
# - Automatic state locking prevents concurrent modifications
# - Easy to share state across teams
#
# APPROACH 2: Google Cloud Storage (GCS)
# - Each environment/instance gets its own bucket or state file
# - Works well with Google Cloud Platform
# - Requires less third-party account management
#
# ============================================================================
# APPROACH 1: Terraform Cloud (Uncomment to use)
# ============================================================================
#
# terraform {
#   cloud {
#     organization = "your-org-name"  # Change this to your Terraform Cloud org
#
#     workspaces {
#       name = "resume-customizer-${var.environment}"  # Creates separate workspace per env
#     }
#   }
# }
#
# Then in terraform.tfvars add:
#   environment = "dev"    # or "staging", "prod", etc.
#
# Usage:
#   terraform init                    # Links to Terraform Cloud
#   terraform workspace list          # See all workspaces
#   terraform workspace select prod   # Switch environments
#
# ============================================================================
# APPROACH 2: Google Cloud Storage (Uncomment to use)
# ============================================================================
#
# terraform {
#   backend "gcs" {
#     bucket = "your-terraform-state-bucket"  # Must exist beforehand
#     prefix = "resume-customizer/${environment}"  # Separate path per env
#   }
# }
#
# Setup (run once per project):
#   gsutil mb gs://your-terraform-state-bucket
#
# Usage with different environments:
#   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
#   terraform init -backend-config="prefix=resume-customizer/dev"
#   terraform apply
#
# Then for staging:
#   terraform init -backend-config="prefix=resume-customizer/staging"
#   terraform apply
#
# ============================================================================
# LOCAL STATE (Default - Use ONLY for development/testing)
# ============================================================================
#
# If no backend is configured, Terraform uses local state (terraform.tfstate).
# This is DANGEROUS for multi-instance deployments because:
# - State is not shared between instances
# - Running terraform destroy will only affect local resources
# - State can get out of sync with actual infrastructure
#
# DO NOT USE THIS FOR PRODUCTION MULTI-INSTANCE DEPLOYMENTS.

# ============================================================================
# RECOMMENDED SETUP FOR YOUR MULTI-INSTANCE DEPLOYMENT
# ============================================================================
#
# 1. Create a Terraform Cloud account at https://app.terraform.io
# 2. Create an organization
# 3. Generate an API token
# 4. Create ~/.terraformrc with your API token:
#    credentials "app.terraform.io" {
#      token = "your-api-token-here"
#    }
# 5. Uncomment the Terraform Cloud configuration above
# 6. Add to terraform.tfvars:
#    environment = "dev"  # (or "staging", "prod", etc.)
# 7. Run: terraform init
# 8. For each environment, either:
#    - Use terraform workspace select <env-name>
#    - Or create different terraform.tfvars files per environment
#
# This prevents accidental destruction across environments.
