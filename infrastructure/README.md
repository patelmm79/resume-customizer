# Cloud Deployment Infrastructure

This directory contains Terraform templates for setting up cloud storage for Resume Customizer settings persistence.

## Overview

In cloud deployments (Streamlit Cloud, AWS, Google Cloud, etc.), the application's filesystem is typically ephemeral and doesn't persist between app restarts or redeploys. This directory provides Infrastructure-as-Code (IaC) templates to set up persistent cloud storage for the `.settings.json` configuration file.

## Why Cloud Storage?

- **Ephemeral Filesystems**: Serverless and containerized environments don't persist local files
- **Multi-Instance Deployments**: Multiple app instances can share settings
- **Across Redeploys**: Settings survive application redeployments
- **Automatic Persistence**: UI changes to settings are saved immediately

## Supported Cloud Providers

- **AWS S3** (`terraform-s3.tf`)
- **Google Cloud Storage** (`terraform-gcs.tf`)

## Quick Start

### Prerequisites

- Terraform >= 1.0
- AWS CLI or Google Cloud CLI (depending on provider)
- Appropriate cloud credentials configured

### AWS S3 Setup

```bash
# Initialize Terraform
terraform init

# Review the plan (optional)
terraform plan -var="aws_region=us-west-2" \
               -target=aws_s3_bucket.settings \
               -f terraform-s3.tf

# Create S3 bucket and IAM role
terraform apply -f terraform-s3.tf

# Get outputs for environment configuration
terraform output
```

**Environment Variables** (add to `.env` or Streamlit Secrets):
```bash
RESUME_SETTINGS_STORAGE=s3
RESUME_SETTINGS_BUCKET=<bucket-name-from-output>
AWS_REGION=<region-from-output>
```

### Google Cloud Storage Setup

```bash
# Initialize Terraform
terraform init

# Review the plan (optional)
terraform plan -var="gcp_project=my-project" \
               -f terraform-gcs.tf

# Create GCS bucket and service account
terraform apply -var="gcp_project=my-project" \
                -f terraform-gcs.tf

# Get outputs for environment configuration
terraform output -f terraform-gcs.tf
```

**Environment Variables** (add to `.env` or Streamlit Secrets):
```bash
RESUME_SETTINGS_STORAGE=gcs
RESUME_SETTINGS_BUCKET=<bucket-name-from-output>
GOOGLE_CLOUD_PROJECT=<project-id>
```

## Deployment Platforms

### Streamlit Cloud

1. **Create Storage**: Follow AWS or GCS setup above
2. **Add Secrets**: In Streamlit Cloud dashboard:
   - Go to Settings → Secrets
   - Add environment variables from terraform output:
     ```
     RESUME_SETTINGS_STORAGE=s3
     RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
     AWS_REGION=us-west-2
     ```
3. **AWS Credentials** (for S3):
   - Create IAM user with S3 permissions
   - Add credentials as secrets:
     ```
     AWS_ACCESS_KEY_ID=...
     AWS_SECRET_ACCESS_KEY=...
     ```

### AWS EC2 / ECS / Lambda

1. **Create Storage**: Run terraform-s3.tf
2. **Create IAM Role**: Terraform creates this automatically
3. **Attach to Instance**:
   - EC2: Assign IAM role to instance
   - ECS: Reference role in task definition
   - Lambda: Attach role to function
4. **Add Environment Variables**: Set from terraform output

### Google Cloud Run / Cloud Functions

1. **Create Storage**: Run terraform-gcs.tf
2. **Create Service Account**: Terraform creates this automatically
3. **Deploy Application**:
   - Set service account on Cloud Run service or Cloud Function
   - Add environment variables from terraform output

### Docker / Kubernetes

1. **Create Storage**: Run appropriate Terraform template
2. **Set Environment Variables**:
   ```bash
   docker run \
     -e RESUME_SETTINGS_STORAGE=s3 \
     -e RESUME_SETTINGS_BUCKET=my-bucket \
     -e AWS_REGION=us-west-2 \
     -e AWS_ACCESS_KEY_ID=... \
     -e AWS_SECRET_ACCESS_KEY=... \
     resume-customizer:latest
   ```
3. **For Kubernetes (AWS)**:
   - Use IRSA (IAM Roles for Service Accounts)
   - Modify IAM trust policy in Terraform

## Local Development

For local development, **you don't need cloud storage**:

1. Leave `RESUME_SETTINGS_STORAGE` unset or set to `local`
2. Settings will be saved to `.settings.json` locally
3. `.settings.json` is in `.gitignore` (keep personal settings private)

## Architecture

```
┌─────────────────────────────────┐
│   Resume Customizer App         │
└──────────────┬──────────────────┘
               │
        ┌──────▼──────┐
        │   Settings  │
        │   Module    │
        └──────┬──────┘
               │
        ┌──────▼──────────────┐
        │ Check Storage Type: │
        │ - S3 (AWS)          │
        │ - GCS (Google)      │
        │ - Local (default)   │
        └──────┬──────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
   [S3]      [GCS]     [Local]
    │          │          │
    └──────────┼──────────┘
               │
         [.settings.json]
```

## Fallback Behavior

If cloud storage fails (e.g., credentials missing, network error):
- **Save**: Falls back to local `.settings.json`
- **Load**: First tries cloud, then falls back to local, then to defaults
- **Graceful Degradation**: App continues working with local settings

## Cost Considerations

- **S3**: ~$0.023 per GB/month (very cheap for small config files)
- **GCS**: ~$0.020 per GB/month (very cheap for small config files)
- **Network**: Minimal data transfer (config file is <1KB)

## Security Best Practices

1. **Use IAM Roles**: Never use long-lived access keys if possible
2. **Limit Permissions**: Apply principle of least privilege
3. **Encryption**: Both S3 and GCS support encryption at rest
4. **Versioning**: Enabled in both templates for recovery
5. **Public Access**: Blocked in both templates
6. **Service Accounts**: Use for GCP deployments instead of user credentials

## Troubleshooting

### Settings not persisting
1. Verify environment variables are set
2. Check cloud credentials are configured
3. Verify bucket exists and has correct permissions
4. Check application logs for cloud storage errors

### Permission denied errors
1. Verify IAM role/service account has correct permissions
2. For S3: Ensure bucket policy allows access
3. For GCS: Verify service account is bound to bucket

### Bucket already exists error
- Change bucket name in terraform variables
- Or destroy existing bucket: `terraform destroy`

## Cleanup

To remove cloud storage infrastructure:

```bash
# AWS
terraform destroy -f terraform-s3.tf

# Google Cloud
terraform destroy -var="gcp_project=my-project" -f terraform-gcs.tf
```

## Further Reading

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
