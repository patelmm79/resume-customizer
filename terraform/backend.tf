# Terraform Backend Configuration - Google Cloud Storage (GCS)
#
# This configuration stores Terraform state in Google Cloud Storage,
# enabling safe multi-instance/multi-environment deployments.
#
# SETUP INSTRUCTIONS:
#
# 1. Create a GCS bucket to store state (run once per GCP project):
#    ```bash
#    gsutil mb gs://your-project-id-terraform-state
#    ```
#    Replace "your-project-id-terraform-state" with a unique bucket name
#
# 2. Update the bucket name below in the backend configuration
#
# 3. Configure per-environment state isolation:
#    Each environment (dev, staging, prod) gets its own state file path
#
# 4. Run terraform init to connect to the backend:
#    ```bash
#    cd terraform
#    terraform init \
#      -backend-config="bucket=your-project-id-terraform-state" \
#      -backend-config="prefix=resume-customizer/dev"
#    ```
#
# 5. For each environment, use a different prefix:
#    - dev:     terraform init -backend-config="prefix=resume-customizer/dev"
#    - staging: terraform init -backend-config="prefix=resume-customizer/staging"
#    - prod:    terraform init -backend-config="prefix=resume-customizer/prod"
#
# RESULT:
# - Each environment has completely isolated state
# - Running 'terraform destroy' only affects that environment
# - Multiple instances can safely run independently

terraform {
  backend "gcs" {
    # IMPORTANT: Replace with your actual bucket name
    # bucket = "your-project-id-terraform-state"

    # prefix is set via -backend-config during terraform init
    # This allows the same configuration to be used across multiple environments
    # Example prefixes:
    # - resume-customizer/dev
    # - resume-customizer/staging
    # - resume-customizer/prod
  }
}

# ============================================================================
# ALTERNATIVE: Terraform Cloud Backend
# ============================================================================
#
# If you prefer Terraform Cloud instead, comment out the "backend "gcs"" block
# above and uncomment the following:
#
# terraform {
#   cloud {
#     organization = "your-org-name"  # Your Terraform Cloud organization
#
#     workspaces {
#       # Creates workspaces like: resume-customizer-dev, resume-customizer-staging
#       name = "resume-customizer-${var.environment}"
#     }
#   }
# }
#
# Setup for Terraform Cloud:
# 1. Create account at https://app.terraform.io
# 2. Create organization
# 3. Generate API token
# 4. Create ~/.terraformrc with:
#    credentials "app.terraform.io" {
#      token = "your-api-token-here"
#    }
# 5. Run: terraform init
#
