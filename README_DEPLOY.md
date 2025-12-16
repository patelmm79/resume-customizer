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

Cloud Build GitHub trigger via Terraform

1. Install the Google Cloud Build GitHub App on the GitHub repository you want to build. Follow the steps in the Cloud Build docs to install the app and authorize access to the repository.

2. Obtain the GitHub App installation id for the repository. You can find this in the GitHub app installation details or via the GitHub API.

3. Configure the GitHub trigger variables in `terraform/terraform.tfvars` (see `terraform/terraform.tfvars.example`). Set `github_owner`, `github_repo`, and `github_branch`.

4. Apply Terraform; the trigger will be created and will run `cloudbuild.yaml` on pushes to the configured branch if your project is already connected to GitHub via the Cloud Build GitHub App. If you have not installed the GitHub App, you can either install it or create the trigger manually in the Cloud Console.

Permissions notes and common errors
- If you see an error like `artifactregistry.repositories.downloadArtifacts denied` when creating the Cloud Run service, the Cloud Run runtime (and/or the Cloud Run service account) does not have read access to the Artifact Registry repository. To fix this Terraform now adds IAM bindings to grant `roles/artifactregistry.reader` to:
	- the service account created for Cloud Run (`resume-customizer-sa`), and
	- the Cloud Run runtime service agent (`service-<PROJECT_NUMBER>@gcp-sa-run.iam.gserviceaccount.com`).

- If you still see permission errors after `terraform apply`, run the following to verify the project number and that bindings exist:

```bash
gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)'
gcloud artifacts repositories describe ${REPO} --location=${REGION}
gcloud projects get-iam-policy ${PROJECT_ID} --format=json | jq '.bindings[] | select(.role=="roles/artifactregistry.reader")'
```

If bindings are missing, add them manually (example):

```bash
# grant repo reader to the Cloud Run service account
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
	--member="serviceAccount:resume-customizer-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
	--role="roles/artifactregistry.reader"

# grant repo reader to Cloud Run runtime agent (use project number from describe)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
	--member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-run.iam.gserviceaccount.com" \
	--role="roles/artifactregistry.reader"
```

Note on the Cloud Run runtime service account: the service account `service-<PROJECT_NUMBER>@gcp-sa-run.iam.gserviceaccount.com` is a Google-managed runtime agent that may be created only after the Cloud Run API is enabled and the Cloud Run service is first created or the service agent is provisioned. If Terraform attempts to bind IAM to that account before it exists you'll see an error like "service account ... does not exist". The Terraform configuration now includes a local wait loop that polls for that service account before applying the repository IAM binding; ensure you have `gcloud` installed and authenticated when running `terraform apply` so the wait can succeed.

Trigger creation errors (invalid argument)
- If the Cloud Build trigger creation fails with "invalid argument", confirm that your project is connected to GitHub via the Cloud Build GitHub App in the Cloud Console (Cloud Build -> Connections). Terraform assumes a pre-existing GitHub connection; if you prefer Terraform to manage the connection you'll need to create a Cloud Build connection resource first or create the trigger manually in the console.
