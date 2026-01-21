@echo off
REM Quick deployment script for Resume Customizer settings persistence (Windows)
REM Usage: deploy-settings.bat [s3|gcs] [region/project]

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ====================================================
echo Resume Customizer Settings Persistence Deployment
echo ====================================================
echo.

REM Check prerequisites
where terraform >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Terraform not found. Please install Terraform first.
    exit /b 1
)
echo [OK] Terraform found

REM Validate cloud provider
if "%1"=="" (
    echo.
    echo Select cloud provider:
    echo   1) AWS S3
    echo   2) Google Cloud Storage (GCS)
    set /p choice="Enter choice [1 or 2]: "

    if "!choice!"=="1" set provider=s3
    if "!choice!"=="2" set provider=gcs
) else (
    set provider=%1
)

if not "!provider!"=="s3" if not "!provider!"=="gcs" (
    echo ERROR: Invalid cloud provider. Use 's3' or 'gcs'
    exit /b 1
)

REM Setup S3
if "!provider!"=="s3" (
    echo.
    echo Setting up AWS S3 bucket...

    if "%2"=="" (
        set region=us-west-2
    ) else (
        set region=%2
    )

    echo AWS Region: !region!

    REM Check AWS CLI
    where aws >nul 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: AWS CLI not found. Make sure AWS credentials are configured.
    ) else (
        REM Verify AWS credentials
        for /f "tokens=*" %%A in ('aws sts get-caller-identity --query Account --output text 2^>nul') do (
            echo [OK] AWS credentials verified (Account: %%A)
        )
    )

    REM Remove GCS config if exists
    if exist terraform-gcs.tf del terraform-gcs.tf

    REM Create tfvars
    (
        echo aws_region = "!region!"
        echo app_name   = "resume-customizer"
    ) > terraform.tfvars

    echo [OK] Created terraform.tfvars
)

REM Setup GCS
if "!provider!"=="gcs" (
    echo.
    echo Setting up Google Cloud Storage bucket...

    if "%2"=="" (
        for /f "tokens=*" %%A in ('gcloud config get-value project 2^>nul') do set project=%%A
        if "!project!"=="" (
            echo ERROR: No GCP project configured. Please specify project ID.
            echo Usage: deploy-settings.bat gcs your-project-id
            exit /b 1
        )
    ) else (
        set project=%2
    )

    echo GCP Project: !project!

    REM Verify GCP credentials
    where gcloud >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: gcloud CLI not found
        exit /b 1
    )

    REM Remove S3 config if exists
    if exist terraform-s3.tf del terraform-s3.tf

    REM Create tfvars
    (
        echo gcp_project = "!project!"
        echo gcp_region  = "us-central1"
        echo app_name    = "resume-customizer"
    ) > terraform.tfvars

    echo [OK] Created terraform.tfvars
)

REM Deploy infrastructure
echo.
echo Initializing Terraform...
call terraform init
echo [OK] Terraform initialized
echo.

echo Planning deployment...
call terraform plan -out=tfplan
echo [OK] Plan created
echo.

set /p response="Apply? This will create cloud resources [y/N]: "
if /i not "!response!"=="y" (
    echo Deployment cancelled
    if exist tfplan del tfplan
    exit /b 0
)

echo.
echo Applying Terraform configuration...
call terraform apply tfplan
if exist tfplan del tfplan
echo [OK] Cloud resources created
echo.

echo ====================================================
echo Deployment Complete!
echo ====================================================
echo.
echo Environment Variables to Set:
echo.
for /f "tokens=*" %%A in ('terraform output -json environment_vars 2^>nul') do (
    echo %%A
)
echo.

echo Additional Information:
for /f "tokens=*" %%A in ('terraform output -raw bucket_name 2^>nul') do (
    echo   Bucket Name: %%A
)

if exist terraform-s3.tf (
    for /f "tokens=*" %%A in ('terraform output -raw iam_role_arn 2^>nul') do (
        echo   IAM Role ARN: %%A
    )
    for /f "tokens=*" %%A in ('terraform output -raw bucket_region 2^>nul') do (
        echo   Region: %%A
    )
) else (
    for /f "tokens=*" %%A in ('terraform output -raw service_account_email 2^>nul') do (
        echo   Service Account: %%A
    )
    for /f "tokens=*" %%A in ('terraform output -raw bucket_location 2^>nul') do (
        echo   Location: %%A
    )
)

echo.
echo Next Steps:
echo   1. Copy the environment variables above
echo   2. Add them to your cloud deployment platform
echo   3. Add cloud credentials to your platform secrets
echo   4. Deploy your app and test settings persistence
echo.
echo For detailed instructions, see: SETTINGS_PERSISTENCE_GUIDE.md
echo.

endlocal
