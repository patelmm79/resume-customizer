# Settings Persistence Deployment Guide

This guide explains how to deploy the Resume Customizer with persistent settings storage using cloud infrastructure (AWS S3 or Google Cloud Storage).

## Overview

The Resume Customizer uses a three-tier settings fallback strategy:
1. **Cloud Storage** (S3 or GCS) - Persists across deployments
2. **Local `.settings.json`** - For development
3. **Built-in Defaults** - Always available as fallback

The `.settings.json` file is `.gitignored` for security, so cloud deployments **must use cloud storage** to maintain settings persistence.

## Prerequisites

### For AWS S3 Deployment
- AWS account with appropriate credentials
- Terraform installed (`terraform --version`)
- AWS CLI configured with credentials

### For Google Cloud Storage (GCS) Deployment
- Google Cloud project created
- `gcloud` CLI installed and authenticated
- Terraform installed

## Quick Start: AWS S3 Deployment

### Step 1: Initialize Terraform with S3 Configuration

```bash
cd infrastructure
terraform init
```

### Step 2: Create terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
aws_region = "us-west-2"      # Change to your preferred AWS region
app_name   = "resume-customizer"
EOF
```

### Step 3: Review and Apply

```bash
# Review what Terraform will create
terraform plan

# Create AWS resources (S3 bucket, IAM role, policies)
terraform apply
```

### Step 4: Capture Output

After `terraform apply` completes, Terraform will output the environment variables needed:

```
Outputs:

bucket_name = "resume-customizer-settings-123456789"
bucket_region = "us-west-2"
environment_vars = {
  "AWS_REGION" = "us-west-2"
  "RESUME_SETTINGS_BUCKET" = "resume-customizer-settings-123456789"
  "RESUME_SETTINGS_STORAGE" = "s3"
}
```

### Step 5: Configure Your Cloud Deployment

Set these environment variables in your cloud deployment (Streamlit Cloud, Heroku, Railway, etc.):

```bash
RESUME_SETTINGS_STORAGE=s3
RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
AWS_REGION=us-west-2
```

**Note**: Your deployment platform needs AWS credentials to access S3. This is typically done via:
- IAM role (if running on AWS EC2, Lambda, etc.)
- AWS access keys (create them in AWS IAM console, then add as secrets)

## Quick Start: Google Cloud Storage (GCS) Deployment

### Step 1: Update Variables for GCS

Edit `terraform.tfvars`:

```bash
cat > terraform.tfvars << 'EOF'
gcp_project = "your-gcp-project-id"
gcp_region  = "us-central1"
app_name    = "resume-customizer"
EOF
```

### Step 2: Switch Terraform Configuration

The infrastructure directory contains both S3 and GCS configurations. Use only one:

```bash
# For GCS (remove S3 config)
cd infrastructure
rm terraform-s3.tf
```

### Step 3: Initialize and Apply

```bash
terraform init
terraform plan
terraform apply
```

### Step 4: Capture Output

After applying, note the environment variables:

```
Outputs:

bucket_name = "resume-customizer-settings-your-gcp-project-id"
service_account_email = "resume-customizer-settings-sa@your-gcp-project.iam.gserviceaccount.com"
environment_vars = {
  "GOOGLE_CLOUD_PROJECT" = "your-gcp-project-id"
  "RESUME_SETTINGS_BUCKET" = "resume-customizer-settings-your-gcp-project-id"
  "RESUME_SETTINGS_STORAGE" = "gcs"
}
```

### Step 5: Configure Your Cloud Deployment

Set these environment variables in your deployment:

```bash
RESUME_SETTINGS_STORAGE=gcs
RESUME_SETTINGS_BUCKET=resume-customizer-settings-your-gcp-project-id
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

Your deployment platform needs GCP service account credentials. Create and download a service account key, then add as a secret.

## Deployment Examples

### Example: Streamlit Cloud with AWS S3

1. Deploy your app to Streamlit Cloud normally
2. Add Secrets in Streamlit Cloud dashboard (Settings → Secrets):
   ```
   RESUME_SETTINGS_STORAGE = s3
   RESUME_SETTINGS_BUCKET = resume-customizer-settings-123456789
   AWS_REGION = us-west-2
   AWS_ACCESS_KEY_ID = your-aws-access-key
   AWS_SECRET_ACCESS_KEY = your-aws-secret-key
   ```

### Example: Heroku with AWS S3

```bash
heroku config:set RESUME_SETTINGS_STORAGE=s3
heroku config:set RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
heroku config:set AWS_REGION=us-west-2
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### Example: Railway with GCS

1. Add environment variables in Railway dashboard:
   ```
   RESUME_SETTINGS_STORAGE=gcs
   RESUME_SETTINGS_BUCKET=resume-customizer-settings-your-gcp-project-id
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json
   ```

2. Create GCP service account key and add as Railway secret

## Security Best Practices

### AWS S3

1. **Use IAM Roles**: If running on AWS infrastructure, use IAM roles instead of access keys
2. **Encrypt Credentials**: Never commit AWS credentials to git
3. **Use Secrets Management**: Store credentials in your deployment platform's secrets manager
4. **Restrict Bucket Access**: The Terraform policy only allows access to `.settings.json` file
5. **Enable Versioning**: The bucket has versioning enabled for recovery

### Google Cloud Storage

1. **Use Service Accounts**: Create dedicated service account for app access
2. **Use Workload Identity**: If on GKE, use Workload Identity instead of service account keys
3. **Rotate Keys Regularly**: Service account keys should be rotated periodically
4. **Use IAM Bindings**: Limit permissions to only what's needed
5. **Enable Versioning**: The bucket has versioning enabled for recovery

## Verification

After deployment, verify settings persistence works:

1. **Open the app** and go to Settings
2. **Change a setting** (e.g., select a different LLM provider)
3. **Restart the app** (or refresh in cloud deployment)
4. **Verify the setting persisted** (should still show your choice)

## Troubleshooting

### Settings Not Persisting

**Check 1**: Verify environment variables are set
```bash
echo $RESUME_SETTINGS_STORAGE
echo $RESUME_SETTINGS_BUCKET
```

**Check 2**: Check app logs for error messages
Look for: `[WARNING] Failed to save to cloud storage`

**Check 3**: Verify cloud credentials are working
- For S3: `aws s3 ls` (verify AWS access)
- For GCS: `gsutil ls` (verify GCP access)

**Check 4**: Verify IAM permissions
- For S3: Ensure policy allows `s3:GetObject` and `s3:PutObject` on `.settings.json`
- For GCS: Ensure service account has `storage.objectAdmin` role

### Terraform Errors

**Error: "provider not configured"**
```bash
terraform init
```

**Error: "bucket already exists"**
Use a different `app_name` in `terraform.tfvars` or change AWS region

**Error: "access denied"**
Ensure your AWS/GCP credentials have sufficient permissions

## Clean Up

To destroy cloud resources (when no longer needed):

```bash
cd infrastructure
terraform destroy
```

**Warning**: This will delete the S3/GCS bucket and any stored settings!

## How Settings Persistence Works

### Load Flow
1. App starts → `load_settings()`
2. DEFAULT_SETTINGS loaded (from code)
3. If `RESUME_SETTINGS_STORAGE=s3/gcs` → Attempt cloud load
4. If cloud unavailable → Fall back to local `.settings.json`
5. If local unavailable → Use defaults
6. Final settings = defaults + overrides from cloud/local

### Save Flow
1. User changes setting in UI
2. `save_settings(updated_settings)` called
3. If `RESUME_SETTINGS_STORAGE=s3/gcs` → Save to cloud first
4. If cloud save succeeds → Done
5. If cloud save fails → Fall back to local save
6. Graceful degradation ensures settings are always saved somewhere

### Example: Adding a New LLM Model

1. User adds "ollama" provider in Settings UI
2. App calls `add_provider("ollama", ["llama3:70b"], ...)`
3. Settings updated in memory
4. `save_settings()` called
5. If S3/GCS configured → Settings saved to `s3://bucket/.settings.json` or `gs://bucket/.settings.json`
6. On restart → Settings loaded from cloud, ollama provider still available
7. If cloud unavailable → Settings saved locally, restored from `.settings.json`

## Environment Variables Reference

### Application Settings
```bash
# Storage type: 'local' (default), 's3', or 'gcs'
RESUME_SETTINGS_STORAGE=s3

# Bucket name for storing .settings.json
RESUME_SETTINGS_BUCKET=your-bucket-name

# Optional: Custom path in bucket (default: .settings.json)
RESUME_SETTINGS_KEY=.settings.json
```

### AWS Configuration (if using S3)
```bash
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key          # If not using IAM role
AWS_SECRET_ACCESS_KEY=your-secret-key      # If not using IAM role
```

### Google Cloud Configuration (if using GCS)
```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Next Steps

- Deploy your app to your chosen platform
- Set the environment variables
- Test settings persistence by making changes and restarting
- Monitor logs for any persistence issues
- Set up backup strategy for your settings bucket (versioning is enabled by default)
