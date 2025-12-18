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

CI / Automated builds (Terraform-managed)

This repository uses Terraform to trigger an in-cloud Cloud Build during `terraform apply`. The configuration now uses a `google_cloudbuild_build` resource which runs the build inside Cloud Build (build -> push -> deploy). This works correctly when Terraform is executed remotely (Terraform Cloud / GCP) and does not require `gcloud` on the machine running Terraform.

Requirements for Terraform-managed builds
- The Cloud Build service account must have permission to push to the Artifact Registry repository and to deploy Cloud Run (the Terraform config adds a repository-level writer binding for Cloud Build).

How it runs
1. On `terraform apply` executed remotely, Terraform creates a `google_cloudbuild_build` resource. Cloud Build performs the container build, pushes the image to Artifact Registry, and deploys the new image to Cloud Run.
2. Terraform then creates any remaining resources and finalizes the Cloud Run service.

If you prefer CI-driven builds via GitHub Actions or Cloud Build triggers, you can instead remove the `google_cloudbuild_build` and use an external CI pipeline that builds and pushes images, then run Terraform to update the service image.

Note on the Cloud Run runtime service account: the service account `service-<PROJECT_NUMBER>@gcp-sa-run.iam.gserviceaccount.com` is a Google-managed runtime agent that may be created only after the Cloud Run API is enabled and the Cloud Run service is first created or the service agent is provisioned. If Terraform attempts to bind IAM to that account before it exists you'll see an error like "service account ... does not exist". The Terraform configuration now includes a local wait loop that polls for that service account before applying the repository IAM binding; ensure you have `gcloud` installed and authenticated when running `terraform apply` so the wait can succeed.

Trigger creation errors (invalid argument)
- If the Cloud Build trigger creation fails with "invalid argument", confirm that your project is connected to GitHub via the Cloud Build GitHub App in the Cloud Console (Cloud Build -> Connections). Terraform assumes a pre-existing GitHub connection; if you prefer Terraform to manage the connection you'll need to create a Cloud Build connection resource first or create the trigger manually in the console.

Secrets & runtime configuration (recommended)
-------------------------------------------

This project requires provider API keys (LLM providers) and some runtime tuning values. For production deployments we recommend storing sensitive values in Secret Manager and mapping them into Cloud Run at runtime rather than committing them to source control or Terraform state.

1. Secret naming and `secret_prefix`
	- The Terraform example `terraform.tfvars.example` includes a `secret_prefix` variable used to name secrets in Secret Manager to avoid collisions (for example `resume_customizer-prod-GEMINI_API_KEY`).
	- Fill `secret_prefix` in your `terraform.tfvars` per-environment (e.g. `resume_customizer-staging`).

2. Terraform behavior
	- Terraform will create Secret Manager secret resources for standard keys (if `create_secrets = true`) but will NOT populate secret versions. This avoids storing secret values in Terraform state.
	- After `terraform apply`, you should populate secret values with `gcloud secrets versions add` or via CI (recommended).

3. Adding secret values (example)
```bash
# Example: add a Gemini key value to Secret Manager
SECRET_PREFIX=resume_customizer-prod
echo -n "$GEMINI_API_KEY" | \
  gcloud secrets versions add "${SECRET_PREFIX}-GEMINI_API_KEY" --data-file=- --project=${PROJECT_ID}

# Add other keys similarly:
echo -n "$ANTHROPIC_API_KEY" | gcloud secrets versions add "${SECRET_PREFIX}-ANTHROPIC_API_KEY" --data-file=- --project=${PROJECT_ID}
echo -n "$CUSTOM_LLM_API_KEY" | gcloud secrets versions add "${SECRET_PREFIX}-CUSTOM_LLM_API_KEY" --data-file=- --project=${PROJECT_ID}
```

4. Grant access to Cloud Run service account
```bash
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
# If using a custom service account set in Terraform use that; otherwise use default runtime SA
RUN_SA=service-${PROJECT_NUMBER}@gcp-sa-run.iam.gserviceaccount.com

gcloud secrets add-iam-policy-binding "${SECRET_PREFIX}-GEMINI_API_KEY" \
  --member="serviceAccount:${RUN_SA}" --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID}
```

5. CI-driven secret provisioning (recommended)
	- Add your secret values to your CI provider (GitHub Actions secrets, Cloud Build substitutions, etc.).
	- In CI, run `gcloud secrets versions add` for each secret (as above) before running `terraform apply` or `gcloud run deploy` so the runtime has access immediately after deployment.

6. Non-sensitive runtime values
	- Non-sensitive settings such as model names and tuning parameters (`gemini_model`, `claude_model`, `custom_llm_max_retries`, `custom_llm_context_limit`) are exposed as standard environment variables via Terraform and should be set in `terraform.tfvars`.

7. Security & best practices
	- Do not put secret values into `terraform.tfvars` or commit them.
	- Use the `secret_prefix` to isolate secrets per environment.
	- Rotate keys by adding new secret versions and removing old ones. Use `latest` in the Cloud Run secret mapping to pick up new versions after redeploy.

If you'd like, add a CI script that uploads secret versions from your CI secret store and runs `terraform apply`. This is the recommended pattern to ensure per-deployment secrets are provisioned automatically.
