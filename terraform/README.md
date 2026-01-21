# Resume Customizer Terraform Infrastructure

This directory contains ALL infrastructure-as-code for the Resume Customizer application.

## Directory Structure

```
terraform/
├── main.tf                              ← Google Cloud Run deployment (main app)
├── variables.tf                         ← Variable definitions
├── outputs.tf                           ← Output definitions
├── backend.tf                           ← Terraform backend configuration
├── terraform.tfvars.example             ← GCP Cloud Run configuration example
│
├── README.md                            ← This file
│
# ========== SETTINGS PERSISTENCE (S3/GCS) ==========
├── settings-s3.tf                       ← AWS S3 bucket for settings
├── settings-gcs.tf                      ← Google Cloud Storage bucket for settings
├── settings.tfvars.example              ← Settings persistence configuration example
├── SETTINGS_PERSISTENCE_GUIDE.md        ← Complete guide for settings deployment
│
# ========== DEPLOYMENT SCRIPTS ==========
├── deploy-settings.bat                  ← Windows settings deployment automation
├── deploy-settings.sh                   ← Linux/macOS settings deployment automation
```

## What Each Component Does

### Main Application Infrastructure (GCP Cloud Run)
- **Files**: `main.tf`, `variables.tf`, `outputs.tf`, `backend.tf`
- **Purpose**: Deploys the Resume Customizer app to Google Cloud Run
- **Configuration**: `terraform.tfvars` (Cloud Run settings)
- **Scope**: Full application deployment, CI/CD integration, Cloud Build

### Settings Persistence Infrastructure (S3 or GCS)
- **Files**: `settings-s3.tf`, `settings-gcs.tf`
- **Purpose**: Creates cloud storage bucket for persistent settings
- **Configuration**: `settings.tfvars.example` (choose AWS or GCP)
- **Scope**: ONLY for settings persistence (not the main app)

## Quick Start

### Option 1: Deploy Main Application (GCP Cloud Run)

See `terraform.tfvars.example` for GCP configuration.

```bash
terraform init
terraform plan
terraform apply
```

### Option 2: Deploy Settings Persistence (AWS S3 or Google Cloud Storage)

**Use the automated script (RECOMMENDED):**

Windows:
```bash
deploy-settings.bat
```

Linux/macOS:
```bash
chmod +x deploy-settings.sh
./deploy-settings.sh
```

**Or manual deployment:**

1. Copy `settings.tfvars.example` to `settings.tfvars`
2. Edit to choose AWS S3 or Google Cloud Storage
3. Run:
```bash
terraform init
terraform plan
terraform apply
```

## When to Use Each

### Use `terraform.tfvars.example` (Cloud Run)
- Deploying the full Resume Customizer app to Google Cloud
- Setting up CI/CD with Cloud Build
- Configuring the main application infrastructure

### Use `settings.tfvars.example` (Settings Persistence)
- Adding persistent settings storage to ANY deployment
- Deploying to Streamlit Cloud, Heroku, Railway, etc.
- Ensuring user settings survive app restarts/redeployments
- Works with BOTH AWS S3 and Google Cloud Storage

## Important Notes

### No Conflicts
- Both configurations can exist simultaneously
- Cloud Run deployment (main app) on GCP
- Settings persistence can be AWS S3 or GCS
- They don't interfere with each other

### File Organization
- Settings files are prefixed with `settings-` (e.g., `settings-s3.tf`, `settings-gcs.tf`)
- Cloud Run files are NOT prefixed (e.g., `main.tf`, `variables.tf`)
- This prevents naming conflicts

### Configuration Priority
1. When running deployments, Terraform will try to configure BOTH sets of infrastructure
2. If you only want settings persistence: Comment out Cloud Run variables in tfvars
3. If you only want Cloud Run: Don't set settings persistence variables
4. Terraform won't error if some variables are missing - it will use defaults

## Documentation

- **Full Cloud Run Setup**: See the existing Terraform files and your deployment platform docs
- **Settings Persistence**: See `SETTINGS_PERSISTENCE_GUIDE.md` (complete guide with examples)
- **Quick Settings Deploy**: Run `deploy-settings.sh` or `deploy-settings.bat`
- **Cloud Deployment Quickstart**: See `../CLOUD_DEPLOYMENT_QUICKSTART.md`

## Deployment Scenarios

### Scenario A: Deploy full app to GCP Cloud Run with persistent settings
```bash
# 1. Configure both
terraform.tfvars:
  project = "my-gcp-project"
  region = "us-central1"
  service_name = "resume-customizer"

  gcp_project = "my-gcp-project"    # Add settings
  gcp_region = "us-central1"        # Add settings
  app_name = "resume-customizer"    # Add settings

# 2. Deploy all infrastructure
terraform init
terraform apply
```

### Scenario B: Deploy app to Streamlit Cloud with persistent settings (S3 or GCS)
```bash
# 1. Deploy ONLY settings persistence
cd terraform
deploy-settings.bat  # or deploy-settings.sh

# 2. Set environment variables in Streamlit Cloud secrets
RESUME_SETTINGS_STORAGE=s3
RESUME_SETTINGS_BUCKET=...
AWS_REGION=us-west-2

# 3. Redeploy Streamlit app
```

### Scenario C: Cloud Run deployment with NO persistent settings
```bash
# Use terraform.tfvars normally (don't add settings variables)
terraform init
terraform apply
```

## Troubleshooting

### "Resource already exists"
- Check if buckets/infrastructure already deployed
- Use different `app_name` for new deployments
- Or run `terraform destroy` first (if you want to recreate)

### "Provider not configured"
```bash
terraform init
```

### Settings not persisting
See `SETTINGS_PERSISTENCE_GUIDE.md` Troubleshooting section

## Cost Estimation

### Cloud Run Deployment
- Always free tier available (first 2M invocations/month)
- ~$0-$20/month depending on usage

### Settings Persistence
- S3: ~$0-$1/month
- GCS: ~$0-$1/month
- Extremely cheap (settings file is tiny, <5 KB)

## Files in This Directory

| File | Purpose | When to Use |
|------|---------|-------------|
| `main.tf` | Cloud Run deployment | GCP deployments |
| `variables.tf` | Variable definitions | Always (loaded automatically) |
| `outputs.tf` | Output values | GCP deployments |
| `backend.tf` | Terraform backend | Team collaboration |
| `terraform.tfvars.example` | GCP Cloud Run example | GCP deployments |
| `settings-s3.tf` | AWS S3 configuration | AWS settings storage |
| `settings-gcs.tf` | GCS configuration | Google Cloud settings storage |
| `settings.tfvars.example` | Settings example | Settings persistence |
| `SETTINGS_PERSISTENCE_GUIDE.md` | Complete guide | Settings deployments |
| `deploy-settings.bat` | Windows automation | Settings on Windows |
| `deploy-settings.sh` | Linux/macOS automation | Settings on Linux/macOS |

## Next Steps

1. **For main app deployment**: See `terraform.tfvars.example` (Cloud Run setup)
2. **For settings persistence**: Run `deploy-settings.sh` or `deploy-settings.bat`
3. **For detailed settings guide**: See `SETTINGS_PERSISTENCE_GUIDE.md`
4. **For complete quickstart**: See `../CLOUD_DEPLOYMENT_QUICKSTART.md`
