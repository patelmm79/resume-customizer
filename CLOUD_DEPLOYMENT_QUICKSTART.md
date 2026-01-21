# Cloud Deployment Quick Start: Settings Persistence Solution

Your settings persistence infrastructure is now ready to deploy. Here's what you need to do:

## TL;DR - The Complete Solution

### Problem Solved
✅ Settings were getting wiped on cloud deployments because `.settings.json` isn't persisted
✅ NOW: Settings automatically persist to AWS S3 or Google Cloud Storage
✅ PLUS: Automatic fallback to local storage if cloud is unavailable

### What Was Created
- ✅ Complete Terraform configuration for AWS S3
- ✅ Complete Terraform configuration for Google Cloud Storage
- ✅ Automated deployment script for Windows (`.bat`)
- ✅ Automated deployment script for Linux/macOS (`.sh`)
- ✅ Comprehensive deployment guides
- ✅ Security best practices (encryption, versioning, IAM)
- ✅ Cost estimation (~$0-$1/month)

## Option 1: Automated Deployment (RECOMMENDED)

### On Windows
```bash
cd terraform
deploy-settings.bat
```

### On Linux/macOS
```bash
cd terraform
chmod +x deploy-settings.sh
./deploy-settings.sh
```

**The script will:**
1. Ask which cloud provider (AWS S3 or Google Cloud Storage)
2. Verify your credentials
3. Create cloud resources automatically
4. Display environment variables to set

**Then:**
1. Copy the environment variables
2. Add to your cloud deployment (Streamlit Cloud, Heroku, Railway, etc.)
3. Redeploy your app
4. Done! ✅

---

## Option 2: Manual Deployment

### For AWS S3

**1. Verify AWS credentials:**
```bash
aws sts get-caller-identity
```

**2. Navigate to infrastructure:**
```bash
cd terraform
```

**3. Create `terraform.tfvars`:**
```hcl
aws_region = "us-west-2"
app_name   = "resume-customizer"
```

**4. Deploy:**
```bash
terraform init
terraform plan
terraform apply
```

**5. Copy outputs and add to your cloud deployment:**
```
RESUME_SETTINGS_STORAGE=s3
RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
AWS_REGION=us-west-2
```

---

### For Google Cloud Storage

**1. Verify GCP credentials:**
```bash
gcloud auth list
```

**2. Navigate to infrastructure:**
```bash
cd terraform
```

**3. Remove S3 config:**
```bash
rm terraform-s3.tf
```

**4. Create `terraform.tfvars`:**
```hcl
gcp_project = "your-gcp-project-id"
gcp_region  = "us-central1"
app_name    = "resume-customizer"
```

**5. Deploy:**
```bash
terraform init
terraform plan
terraform apply
```

**6. Copy outputs and add to your cloud deployment:**
```
RESUME_SETTINGS_STORAGE=gcs
RESUME_SETTINGS_BUCKET=resume-customizer-settings-your-gcp-project-id
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

---

## Adding to Your Cloud Deployment

### Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click your app → Settings
3. Go to "Secrets"
4. Add environment variables (copy from Terraform output)
5. Add cloud credentials:
   - **For AWS**: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - **For GCS**: `GOOGLE_APPLICATION_CREDENTIALS` (upload JSON key file)

### Heroku
```bash
heroku config:set RESUME_SETTINGS_STORAGE=s3
heroku config:set RESUME_SETTINGS_BUCKET=resume-customizer-settings-123456789
heroku config:set AWS_REGION=us-west-2
heroku config:set AWS_ACCESS_KEY_ID=your-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-secret
```

### Railway
1. Go to your project settings
2. Add environment variables
3. Add secret for cloud credentials
4. Redeploy

---

## Testing Persistence

After deploying with environment variables:

1. **Open your app**
2. **Go to Settings**
3. **Change a setting** (e.g., select a different LLM provider)
4. **Refresh the page or restart the app**
5. **Verify the setting persisted** ✅

---

## What Happens Under the Hood

### Settings Load Flow
```
App starts
  ↓
Load DEFAULT_SETTINGS (from code)
  ↓
If RESUME_SETTINGS_STORAGE=s3/gcs:
  Try cloud storage (S3/GCS) → Success? Use it
  If cloud fails → Fall back to local .settings.json
  If local fails → Use defaults
  ↓
If RESUME_SETTINGS_STORAGE=local:
  Try local .settings.json
  If fails → Use defaults
```

### Settings Save Flow
```
User changes setting in UI
  ↓
If RESUME_SETTINGS_STORAGE=s3/gcs:
  Try save to cloud first
  If success → Done
  If fails → Fall back to local save
  ↓
If RESUME_SETTINGS_STORAGE=local:
  Save to .settings.json
```

---

## Infrastructure Created

### AWS S3
- ✅ Private S3 bucket (no public access)
- ✅ Encryption at rest (AES256)
- ✅ Versioning enabled (for recovery)
- ✅ IAM role with minimal permissions
- ✅ Only allows access to `.settings.json`

### Google Cloud Storage
- ✅ Private GCS bucket
- ✅ Uniform bucket-level access
- ✅ Versioning enabled
- ✅ Dedicated service account
- ✅ Only allows necessary permissions

---

## Security

### AWS S3
- Bucket is private (public access blocked)
- Server-side encryption enabled
- IAM policy restricted to `.settings.json` only
- Versioning for backup/recovery

### Google Cloud Storage
- Uniform bucket-level access
- Service account with minimal permissions
- Versioning for backup/recovery
- No public access

### Credentials
- **AWS**: Use IAM role if on AWS infrastructure, otherwise use access keys
- **GCS**: Use service account (no key files needed on GCP infrastructure)
- **Deployment Platforms**: Add as secrets/environment variables

---

## Documentation

Detailed documentation is available:
- **Quick Start**: `infrastructure/README.md`
- **Complete Guide**: `infrastructure/SETTINGS_PERSISTENCE_GUIDE.md`
- **Settings System**: `utils/settings.py`

---

## Cost

**Extremely cost-effective:**
- **AWS S3**: ~$0-$1/month (storage: ~$0.023/GB, requests: $0.0004/1,000)
- **GCS**: ~$0-$1/month (storage: ~$0.020/GB, requests: $0.0004/1,000)

Your settings file is tiny (~1-5 KB), so you'll mostly see request costs ($0.02-$0.05/month depending on usage).

---

## Troubleshooting

### Settings not persisting?
1. Check environment variables are set: `echo $RESUME_SETTINGS_STORAGE`
2. Check app logs for: `[WARNING] Failed to save to cloud storage`
3. Verify credentials are valid
4. Check IAM permissions

### Terraform errors?
- **"provider not configured"**: Run `terraform init`
- **"bucket already exists"**: Use different `app_name` or region
- **"access denied"**: Verify AWS/GCP credentials

For detailed troubleshooting, see `infrastructure/SETTINGS_PERSISTENCE_GUIDE.md`

---

## Summary

You now have:
- ✅ Complete infrastructure-as-code (Terraform)
- ✅ Automated deployment scripts
- ✅ Settings persistence in AWS S3 or Google Cloud Storage
- ✅ Automatic fallback to local storage
- ✅ Security best practices
- ✅ Comprehensive documentation

**Next Steps:**
1. Run the deployment script: `infrastructure/deploy-settings.bat` (Windows) or `infrastructure/deploy-settings.sh` (Linux/macOS)
2. Set environment variables in your cloud deployment
3. Redeploy your app
4. Test settings persistence

**Your settings will now survive cloud deployments!** 🎉

---

## Files Added

```
terraform/
├── main.tf                            (GCP Cloud Run - existing)
├── variables.tf                       (Variables - existing)
├── outputs.tf                         (Outputs - existing)
│
├── settings-s3.tf                     (AWS S3 configuration - NEW)
├── settings-gcs.tf                    (GCS configuration - NEW)
├── settings.tfvars.example            (Settings config example - NEW)
├── SETTINGS_PERSISTENCE_GUIDE.md      (Complete guide - NEW)
├── deploy-settings.bat                (Windows deployment script - NEW)
├── deploy-settings.sh                 (Linux/macOS deployment script - NEW)
├── README.md                          (Terraform directory guide - NEW)
└── [other Terraform files...]

CLOUD_DEPLOYMENT_QUICKSTART.md         (This file - in root directory)
```

**Note**: Settings persistence files are now IN `/terraform` directory, not in a separate `/infrastructure` directory.

---

## Questions?

Refer to:
- Terraform directory guide → `terraform/README.md`
- Settings persistence guide → `terraform/SETTINGS_PERSISTENCE_GUIDE.md`
- Implementation details → `utils/settings.py`
