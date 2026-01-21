# Terraform configuration for S3 bucket to store Resume Customizer settings
# This creates an S3 bucket for persisting .settings.json across deployments
# Only created when storage_provider = "s3"

variable "aws_region" {
  description = "AWS region for S3 bucket (only used if storage_provider = 's3')"
  type        = string
  default     = "us-west-2"
}

variable "app_name" {
  description = "Application name for settings storage resource naming"
  type        = string
  default     = "resume-customizer"
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for settings storage
resource "aws_s3_bucket" "settings" {
  count  = var.storage_provider == "s3" ? 1 : 0
  bucket = "${var.app_name}-settings-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.app_name}-settings"
    Environment = "production"
    Purpose     = "Application configuration storage"
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "settings" {
  count  = var.storage_provider == "s3" ? 1 : 0
  bucket = aws_s3_bucket.settings[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for backup/recovery
resource "aws_s3_bucket_versioning" "settings" {
  count  = var.storage_provider == "s3" ? 1 : 0
  bucket = aws_s3_bucket.settings[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "settings" {
  count  = var.storage_provider == "s3" ? 1 : 0
  bucket = aws_s3_bucket.settings[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM role for application to access settings bucket
resource "aws_iam_role" "app_role" {
  count = var.storage_provider == "s3" ? 1 : 0
  name  = "${var.app_name}-settings-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          # Modify this for your use case:
          # - For EC2: AWS Service "ec2.amazonaws.com"
          # - For Lambda: AWS Service "lambda.amazonaws.com"
          # - For Kubernetes (IRSA): AWS Federated "arn:aws:iam::<account>:oidc-provider/..."
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for S3 bucket access
resource "aws_iam_role_policy" "app_s3_policy" {
  count  = var.storage_provider == "s3" ? 1 : 0
  name   = "${var.app_name}-s3-access-policy"
  role   = aws_iam_role.app_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.settings[0].arn}/.settings.json"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.settings[0].arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Outputs (only populated if storage_provider = "s3")
output "s3_bucket_name" {
  description = "S3 bucket name for settings storage"
  value       = var.storage_provider == "s3" ? aws_s3_bucket.settings[0].id : null
}

output "s3_bucket_region" {
  description = "AWS region"
  value       = var.storage_provider == "s3" ? var.aws_region : null
}

output "s3_iam_role_arn" {
  description = "ARN of IAM role for application access"
  value       = var.storage_provider == "s3" ? aws_iam_role.app_role[0].arn : null
}

output "s3_environment_vars" {
  description = "Environment variables to set for application (S3)"
  value = var.storage_provider == "s3" ? {
    RESUME_SETTINGS_STORAGE = "s3"
    RESUME_SETTINGS_BUCKET  = aws_s3_bucket.settings[0].id
    AWS_REGION              = var.aws_region
  } : null
}
