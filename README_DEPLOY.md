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
cd terraform
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

Two-step Terraform flow (optional)

If you'd like to avoid timing issues with the Google-managed Cloud Run runtime service account, use a two-step apply:

1. First apply: set `create_runtime_bindings = false` in `terraform/terraform.tfvars` and run `terraform apply`. This will create the Artifact Registry, service account you control (`resume-customizer-sa`), and other infra but skip binding for the Google-managed runtime agent.

2. Wait for the Cloud Run runtime service account to appear (it may be created when Cloud Run is first used). You can check:

```bash
PROJECT=your-gcp-project-id
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT} --format='value(projectNumber)')
gcloud iam service-accounts describe service-${PROJECT_NUMBER}@gcp-sa-run.iam.gserviceaccount.com --project=${PROJECT}
```

3. Second apply: set `create_runtime_bindings = true` in `terraform/terraform.tfvars` and run `terraform apply` again. Terraform will then create the bindings for the runtime agent.

This two-step approach prevents Terraform from attempting to bind to a Google-managed service account before it exists.

After successful apply, Terraform outputs will include `cloud_run_url`.

Notes
- The Dockerfile launches Streamlit on the port provided by Cloud Run (`PORT` env). Cloud Run will route HTTP requests to the Streamlit app.
- To automate fully (push on commit -> build -> deploy), create a Cloud Build Trigger (GitHub/GCS) and point it to this repo and `cloudbuild.yaml`.

CI / Automated builds

This repo now includes a GitHub Actions workflow to build and deploy on pushes to `main`:

- `.github/workflows/build-deploy.yml`

Required GitHub secrets (set in the repository Settings → Secrets):

- `GCP_SA_KEY`: JSON service account key with permissions to run Cloud Build, push to Artifact Registry, and deploy to Cloud Run (roles: `roles/cloudbuild.builds.builder`, `roles/artifactregistry.writer`, `roles/run.admin`).
- `GCP_PROJECT`: your GCP project id
- `GCP_REGION`: region (e.g., `us-central1`)
- `ARTIFACT_REPO`: Artifact Registry repository id (e.g., `resume-customizer-repo`)

The workflow runs Cloud Build (`gcloud builds submit`) to build and push the image to Artifact Registry and then runs `gcloud run deploy` to deploy the service.

Why I switched from Terraform trigger

The Terraform-managed Cloud Build GitHub trigger was encountering a 400 "invalid argument" due to differences in GitHub connections and Cloud Build API expectations in some projects. Using GitHub Actions keeps CI configuration in GitHub and avoids those connection issues.

If you prefer Cloud Build triggers managed in Terraform, you can still create them manually in the Cloud Console (Cloud Build → Triggers) and remove the GitHub Actions workflow.

Note on the Cloud Run runtime service account: the service account `service-<PROJECT_NUMBER>@gcp-sa-run.iam.gserviceaccount.com` is a Google-managed runtime agent that may be created only after the Cloud Run API is enabled and the Cloud Run service is first created or the service agent is provisioned. If Terraform attempts to bind IAM to that account before it exists you'll see an error like "service account ... does not exist". The Terraform configuration now includes a local wait loop that polls for that service account before applying the repository IAM binding; ensure you have `gcloud` installed and authenticated when running `terraform apply` so the wait can succeed.

Trigger creation errors (invalid argument)
- If the Cloud Build trigger creation fails with "invalid argument", confirm that your project is connected to GitHub via the Cloud Build GitHub App in the Cloud Console (Cloud Build -> Connections). Terraform assumes a pre-existing GitHub connection; if you prefer Terraform to manage the connection you'll need to create a Cloud Build connection resource first or create the trigger manually in the console.
