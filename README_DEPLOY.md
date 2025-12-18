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

This repository uses Terraform to create a Cloud Build Trigger (via `google_cloudbuild_trigger`). The trigger runs the `cloudbuild.yaml` pipeline in Cloud Build when commits are pushed to the configured GitHub branch. This approach works with remote Terraform runs and keeps builds fully in-cloud.

Requirements for Terraform-managed triggers
- The repository must be connected to Cloud Build via the GitHub connection in the Cloud Console (Cloud Build -> Connections). Terraform can create triggers but cannot create the GitHub App connection automatically in most workflows.

How it runs
1. On `terraform apply` Terraform creates a `google_cloudbuild_trigger` that will run Cloud Build on pushes to the configured branch (for example `main`).
2. When you push to the branch, Cloud Build will run the steps defined in `cloudbuild.yaml`, build and push the image, and can deploy the image to Cloud Run as configured in the build steps.

Triggering a build manually
If you need to run the trigger immediately (for example after Terraform creates the trigger), you can run:

```bash
gcloud builds triggers run TRIGGER_ID --branch=main --project=${PROJECT_ID}
```

Replace `TRIGGER_ID` with the trigger ID output by Terraform (or list triggers with `gcloud builds triggers list`).

If you prefer builds to be fully managed by an external CI pipeline (GitHub Actions, Cloud Build triggers on PR merge, etc.), create that pipeline and have it push the built image to Artifact Registry; Terraform will then point Cloud Run at the pushed image.

Note on the Cloud Run runtime service account: the service account `service-<PROJECT_NUMBER>@gcp-sa-run.iam.gserviceaccount.com` is a Google-managed runtime agent that may be created only after the Cloud Run API is enabled and the Cloud Run service is first created or the service agent is provisioned. If Terraform attempts to bind IAM to that account before it exists you'll see an error like "service account ... does not exist". The Terraform configuration now includes a local wait loop that polls for that service account before applying the repository IAM binding; ensure you have `gcloud` installed and authenticated when running `terraform apply` so the wait can succeed.

Trigger creation errors (invalid argument)

Two options:

**Option 1: Manual GitHub Connection (Default)**
- If the Cloud Build trigger creation fails with "invalid argument", confirm that your project is connected to GitHub via the Cloud Build GitHub App in the Cloud Console (Cloud Build -> Connections).
- Then run `terraform apply` again.

**Option 2: Automated GitHub Connection (Recommended for CI/CD)**
- Terraform can now automate the GitHub connection setup for you using a GitHub Personal Access Token.
- This eliminates the need for manual setup in the console.

Steps to automate:

1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Check these scopes:
     - `repo` (full control of private repositories)
     - `admin:repo_hook` (write access to hooks)
   - Click "Generate token" and copy the token value

2. Add to your `terraform.tfvars`:
   ```hcl
   create_github_connection = true
   github_token             = "ghp_xxxxxxxxxxxxxxxxxxxx"  # Your GitHub PAT
   ```

3. Run `terraform apply`:
   ```bash
   terraform apply
   ```

   Terraform will:
   - Create a Secret Manager secret for your GitHub token (not stored in state)
   - Create a Cloud Build GitHub connection
   - Create the trigger using the connection
   - Never expose the token in logs or state

**Security Notes:**
- The `github_token` is marked `sensitive` in Terraform - it won't appear in logs
- The token is stored in Google Cloud Secret Manager, not in Terraform state
- Do NOT commit `terraform.tfvars` to git if it contains your token
- Alternatively, pass the token via environment variable: `export TF_VAR_github_token="ghp_..."`

**Disabling Automation:**
- To go back to manual mode, set `create_github_connection = false` in `terraform.tfvars`

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
