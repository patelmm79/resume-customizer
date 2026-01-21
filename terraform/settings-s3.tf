# Terraform configuration for S3 bucket to store Resume Customizer settings
# This creates an S3 bucket for persisting .settings.json across deployments

# Set AWS region
variable "aws_region" {
  description = "AWS region"
  default     = "us-west-2"
}

# Set application name for resource naming
variable "app_name" {
  description = "Application name (used in resource naming)"
  default     = "resume-customizer"
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for settings storage
resource "aws_s3_bucket" "settings" {
  bucket = "${var.app_name}-settings-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.app_name}-settings"
    Environment = "production"
    Purpose     = "Application configuration storage"
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "settings" {
  bucket = aws_s3_bucket.settings.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for backup/recovery
resource "aws_s3_bucket_versioning" "settings" {
  bucket = aws_s3_bucket.settings.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "settings" {
  bucket = aws_s3_bucket.settings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM role for application to access settings bucket
resource "aws_iam_role" "app_role" {
  name = "${var.app_name}-settings-access-role"

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
  name = "${var.app_name}-s3-access-policy"
  role = aws_iam_role.app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.settings.arn}/.settings.json"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.settings.arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Outputs
output "bucket_name" {
  description = "S3 bucket name for settings storage"
  value       = aws_s3_bucket.settings.id
}

output "bucket_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "iam_role_arn" {
  description = "ARN of IAM role for application access"
  value       = aws_iam_role.app_role.arn
}

output "environment_vars" {
  description = "Environment variables to set for application"
  value = {
    RESUME_SETTINGS_STORAGE = "s3"
    RESUME_SETTINGS_BUCKET  = aws_s3_bucket.settings.id
    AWS_REGION              = var.aws_region
  }
}
