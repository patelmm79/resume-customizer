# Deploying Resume Customizer to Cloud Run

This document explains how to build the container with Cloud Build and deploy the app to Cloud Run using Terraform.

Prerequisites
- Google Cloud SDK installed and authenticated (`gcloud auth login`)
- Terraform installed
- Billing enabled on the GCP project
- APIs will be enabled by Terraform (Cloud Run, Cloud Build, Artifact Registry)

Build & push image using Cloud Build (recommended)

1. Set these environment variables locally:

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export REPO=resume-customizer-repo
export IMAGE_NAME=resume-customizer:latest
export IMAGE=us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}
```

2. Create Artifact Registry repo (Terraform will create it) or create manually:

```bash
# optional: create repo manually
gcloud artifacts repositories create ${REPO} --repository-format=docker --location=${REGION} --description="resume-customizer images"
```

3. Run Cloud Build (this uses `cloudbuild.yaml` in the repo):

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_IMAGE=${IMAGE},_SERVICE_NAME=resume-customizer,_REGION=${REGION} . --project=${PROJECT_ID}
```

Deploy infra with Terraform

1. Initialize Terraform in the `terraform/` folder:

```bash
cd infra
terraform init
```

2. Create a `terraform.tfvars` from the example and set values (ensure `image` matches the pushed image):

```bash
cp terraform.tfvars.example terraform.tfvars
# then edit terraform.tfvars to set your project and image
```

3. Apply Terraform:

```bash
terraform apply
```

After successful apply, Terraform outputs will include `cloud_run_url`.

Notes
- The Dockerfile launches Streamlit on the port provided by Cloud Run (`PORT` env). Cloud Run will route HTTP requests to the Streamlit app.
- To automate fully (push on commit -> build -> deploy), create a Cloud Build Trigger (GitHub/GCS) and point it to this repo and `cloudbuild.yaml`.

Cloud Build GitHub trigger via Terraform

1. Install the Google Cloud Build GitHub App on the GitHub repository you want to build. Follow the steps in the Cloud Build docs to install the app and authorize access to the repository.

2. Obtain the GitHub App installation id for the repository. You can find this in the GitHub app installation details or via the GitHub API.

3. Configure the GitHub trigger variables in `terraform/terraform.tfvars` (see `terraform/terraform.tfvars.example`). Set `github_owner`, `github_repo`, and `github_branch`.

4. Apply Terraform; the trigger will be created and will run `cloudbuild.yaml` on pushes to the configured branch if your project is already connected to GitHub via the Cloud Build GitHub App. If you have not installed the GitHub App, you can either install it or create the trigger manually in the Cloud Console.

Notes on permissions: If you want Terraform to create a GitHub-connected trigger, ensure the Cloud Build GitHub App is installed and authorized for your repository via the Cloud Console first. Alternatively use GitHub Actions or manual triggers.
