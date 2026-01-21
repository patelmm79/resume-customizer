# Infrastructure & Settings Persistence

This directory contains infrastructure-as-code (Terraform) configuration for deploying the Resume Customizer with persistent settings storage.

## Quick Start

### Using the Deployment Script (Recommended)

**On macOS/Linux:**
```bash
cd infrastructure
chmod +x deploy-settings.sh
./deploy-settings.sh
```

**On Windows:**
```bash
cd infrastructure
deploy-settings.bat
```

The script will:
1. Ask which cloud provider to use (AWS S3 or Google Cloud Storage)
2. Configure Terraform automatically
3. Create cloud resources
4. Display environment variables to set in your deployment

### Manual Deployment

**Step 1: Choose your cloud provider**

Remove the configuration file you don't need:
```bash
# For S3: remove GCS config
rm terraform-gcs.tf

# For GCS: remove S3 config
rm terraform-s3.tf
```

**Step 2: Create terraform.tfvars**

For S3:
```hcl
aws_region = "us-west-2"
app_name   = "resume-customizer"
```

For GCS:
```hcl
gcp_project = "your-gcp-project-id"
gcp_region  = "us-central1"
app_name    = "resume-customizer"
```

**Step 3: Deploy**
```bash
terraform init
terraform plan
terraform apply
```

**Step 4: Set Environment Variables**

After deployment, Terraform outputs the environment variables. Set them in your cloud deployment platform:

For S3:
```
RESUME_SETTINGS_STORAGE=s3
RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
AWS_REGION=us-west-2
```

For GCS:
```
RESUME_SETTINGS_STORAGE=gcs
RESUME_SETTINGS_BUCKET=resume-customizer-settings-your-gcp-project-id
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

## Files

- **`terraform-s3.tf`** - AWS S3 configuration (creates bucket, IAM role, security policy)
- **`terraform-gcs.tf`** - Google Cloud Storage configuration (creates bucket, service account)
- **`deploy-settings.sh`** - Automated deployment script (Linux/macOS)
- **`deploy-settings.bat`** - Automated deployment script (Windows)
- **`SETTINGS_PERSISTENCE_GUIDE.md`** - Comprehensive deployment guide with examples
- **`README.md`** - This file

## Architecture

### S3 Deployment
```
┌─────────────────────────────────┐
│     Resume Customizer App       │
│  (deployed on Streamlit Cloud,  │
│   Heroku, Railway, etc.)        │
└──────────────┬──────────────────┘
               │
               │ (with AWS credentials)
               ▼
┌─────────────────────────────────┐
│   AWS S3 Bucket                 │
│  .settings.json (encrypted)     │
│  Versioning Enabled             │
└─────────────────────────────────┘
```

### GCS Deployment
```
┌─────────────────────────────────┐
│     Resume Customizer App       │
│  (deployed on Streamlit Cloud,  │
│   Heroku, Railway, etc.)        │
└──────────────┬──────────────────┘
               │
               │ (with GCP service account)
               ▼
┌─────────────────────────────────┐
│   Google Cloud Storage Bucket   │
│  .settings.json (encrypted)     │
│  Versioning Enabled             │
└─────────────────────────────────┘
```

## Security Features

### All Deployments
- **Encryption**: Files encrypted at rest
- **Versioning**: Previous versions recoverable
- **Access Control**: Only app has access to settings
- **Minimal Permissions**: IAM policies follow least privilege principle

### AWS S3
- **Public Access Block**: Bucket is private
- **Server-Side Encryption**: AES256 encryption by default
- **IAM Role**: Limited to GetObject, PutObject, ListBucket on `.settings.json` only

### Google Cloud Storage
- **Uniform Bucket-Level Access**: Consistent access controls
- **Service Account**: Dedicated account with minimal permissions
- **IAM Binding**: `storage.objectAdmin` role scoped to this bucket

## Credentials & Secrets Management

### AWS S3
Two options:
1. **IAM Role (Recommended)**: If running on AWS infrastructure, use IAM role - no credentials needed
2. **Access Keys**: Create in AWS IAM console, add to deployment platform secrets

### Google Cloud Storage
1. Create service account: `resume-customizer-settings-sa`
2. Create service account key (JSON format)
3. Add to deployment platform secrets as `GOOGLE_APPLICATION_CREDENTIALS`

## Environment Variables

After deployment, set these in your deployment platform:

```bash
# Required (same for both S3 and GCS)
RESUME_SETTINGS_STORAGE=s3       # or 'gcs'
RESUME_SETTINGS_BUCKET=...       # from Terraform output

# AWS S3 specific
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=...            # if not using IAM role
AWS_SECRET_ACCESS_KEY=...        # if not using IAM role

# GCS specific
GOOGLE_CLOUD_PROJECT=...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

## Deployment Platforms

### Streamlit Cloud
1. Deploy app normally
2. Go to app settings → Secrets
3. Add environment variables (copy from Terraform output)
4. Add cloud credentials (AWS keys or GCP key file)
5. Rerun app

### Heroku
```bash
# Set environment variables
heroku config:set RESUME_SETTINGS_STORAGE=s3
heroku config:set RESUME_SETTINGS_BUCKET=...
# Add credentials
heroku config:set AWS_ACCESS_KEY_ID=...
heroku config:set AWS_SECRET_ACCESS_KEY=...
```

### Railway
1. Add environment variables in Dashboard
2. Add secrets (cloud credentials)
3. Redeploy

### Docker / Self-Hosted
Set environment variables in:
- `.env` file
- Docker environment
- Kubernetes ConfigMap/Secret
- Docker Compose

## Troubleshooting

### Settings not persisting
1. Verify environment variables are set: `echo $RESUME_SETTINGS_STORAGE`
2. Check app logs for errors: `[WARNING] Failed to save to cloud storage`
3. Verify cloud credentials are valid
4. Verify IAM permissions are correct

### Terraform errors
- **"provider not configured"**: Run `terraform init`
- **"bucket already exists"**: Use different `app_name` or region
- **"access denied"**: Verify AWS/GCP credentials and permissions

### Can't deploy script
- **Windows**: Make sure running Command Prompt as Administrator
- **Linux/macOS**: Make sure script is executable: `chmod +x deploy-settings.sh`

## Monitoring & Maintenance

### Check storage usage
```bash
# For S3
aws s3 ls s3://resume-customizer-settings-123456789/

# For GCS
gsutil ls gs://resume-customizer-settings-project-id/
```

### View version history
```bash
# For S3
aws s3api list-object-versions --bucket resume-customizer-settings-123456789

# For GCS
gsutil versions ls gs://resume-customizer-settings-project-id/.settings.json
```

### Backup settings
```bash
# For S3
aws s3 cp s3://resume-customizer-settings-123456789/.settings.json ./settings.backup.json

# For GCS
gsutil cp gs://resume-customizer-settings-project-id/.settings.json ./settings.backup.json
```

## Cost Estimation

### AWS S3
- Storage: ~$0.023 per GB/month (typical .settings.json is <1 KB)
- Requests: ~$0.0004 per 1,000 GET requests
- **Estimated monthly cost**: $0-$1

### Google Cloud Storage
- Storage: $0.020 per GB/month
- Requests: $0.0004 per 1,000 requests
- **Estimated monthly cost**: $0-$1

*Both are extremely cost-effective for this use case*

## Cleanup

To destroy all cloud resources:

```bash
cd infrastructure
terraform destroy
```

**Warning**: This is irreversible and will delete stored settings!

## Advanced Topics

### Using Terraform Workspaces
For multiple deployments (dev, staging, prod):

```bash
terraform workspace new staging
terraform workspace select staging
terraform apply
```

### Remote State
Store Terraform state in S3/GCS for team collaboration:

```bash
# Create backend.tf with remote state configuration
# Then run: terraform init
```

### Custom Bucket Names
Edit `terraform-*.tf` to customize bucket naming:

```hcl
bucket = "my-custom-name-${data.aws_caller_identity.current.account_id}"
```

### Adding to Existing Terraform
If you have other Terraform code, copy the relevant resources:
- `aws_s3_bucket`, `aws_iam_role`, `aws_iam_role_policy` (S3)
- `google_storage_bucket`, `google_service_account`, `google_storage_bucket_iam_member` (GCS)

## Support

For issues:
1. Check `SETTINGS_PERSISTENCE_GUIDE.md` for detailed troubleshooting
2. Review Terraform logs: `TF_LOG=DEBUG terraform apply`
3. Check app logs for persistence errors
4. Verify cloud credentials: `aws sts get-caller-identity` or `gcloud auth list`

## References

- [AWS S3 Terraform Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket)
- [Google Cloud Terraform Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket)
- [Resume Customizer Settings](../utils/settings.py)
