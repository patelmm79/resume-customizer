#!/bin/bash
# Quick deployment script for Resume Customizer settings persistence
# Usage: ./deploy-settings.sh [s3|gcs] [region/project]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Resume Customizer Settings Persistence Deployment${NC}\n"

# Check prerequisites
check_prerequisites() {
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}Error: Terraform not found. Please install Terraform first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Terraform found${NC}"
}

# Validate cloud provider
validate_provider() {
    if [[ ! "$1" =~ ^(s3|gcs)$ ]]; then
        echo -e "${RED}Error: Invalid cloud provider. Use 's3' or 'gcs'${NC}"
        echo "Usage: ./deploy-settings.sh [s3|gcs] [region/project-id]"
        exit 1
    fi
}

# Setup S3
setup_s3() {
    local region="${1:-us-west-2}"
    echo -e "${YELLOW}Setting up AWS S3 bucket in region: $region${NC}\n"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${YELLOW}Warning: AWS CLI not found. Make sure you have AWS credentials configured.${NC}"
    else
        # Verify AWS credentials
        if aws sts get-caller-identity &> /dev/null; then
            echo -e "${GREEN}✓ AWS credentials verified${NC}\n"
        else
            echo -e "${RED}Error: AWS credentials not configured${NC}"
            exit 1
        fi
    fi

    # Remove GCS config if exists
    rm -f terraform-gcs.tf

    # Create tfvars
    cat > terraform.tfvars << EOF
aws_region = "$region"
app_name   = "resume-customizer"
EOF

    echo -e "${GREEN}✓ Created terraform.tfvars${NC}\n"
}

# Setup GCS
setup_gcs() {
    local project="${1:-}"

    if [ -z "$project" ]; then
        echo -e "${YELLOW}No GCP project provided. Getting from gcloud...${NC}"
        if command -v gcloud &> /dev/null; then
            project=$(gcloud config get-value project 2>/dev/null)
            if [ -z "$project" ]; then
                echo -e "${RED}Error: No GCP project configured. Please specify project ID.${NC}"
                echo "Usage: ./deploy-settings.sh gcs your-project-id"
                exit 1
            fi
        else
            echo -e "${RED}Error: gcloud CLI not found${NC}"
            exit 1
        fi
    fi

    echo -e "${YELLOW}Setting up Google Cloud Storage bucket in project: $project${NC}\n"

    # Verify GCP credentials
    if gcloud auth list --filter=status:ACTIVE --format='value(account)' &> /dev/null; then
        echo -e "${GREEN}✓ GCP credentials verified${NC}\n"
    else
        echo -e "${RED}Error: GCP credentials not configured${NC}"
        exit 1
    fi

    # Remove S3 config if exists
    rm -f terraform-s3.tf

    # Create tfvars
    cat > terraform.tfvars << EOF
gcp_project = "$project"
gcp_region  = "us-central1"
app_name    = "resume-customizer"
EOF

    echo -e "${GREEN}✓ Created terraform.tfvars${NC}\n"
}

# Deploy infrastructure
deploy() {
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init
    echo -e "${GREEN}✓ Terraform initialized${NC}\n"

    echo -e "${YELLOW}Planning deployment...${NC}"
    terraform plan -out=tfplan
    echo -e "${GREEN}✓ Plan created${NC}\n"

    echo -e "${YELLOW}Apply? (This will create cloud resources) [y/N]${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        rm -f tfplan
        exit 0
    fi

    echo -e "${YELLOW}Applying Terraform configuration...${NC}"
    terraform apply tfplan
    rm -f tfplan
    echo -e "${GREEN}✓ Cloud resources created${NC}\n"

    # Display outputs
    echo -e "${GREEN}Deployment Complete!${NC}\n"
    echo -e "${BLUE}Environment Variables to Set:${NC}"
    terraform output -json environment_vars | jq -r 'to_entries[] | "\(.key)=\(.value)"' | sed 's/^/  /'
    echo ""
    echo -e "${BLUE}Additional Information:${NC}"
    echo "  Bucket Name: $(terraform output -raw bucket_name 2>/dev/null)"
    if [ -f terraform-s3.tf ]; then
        echo "  IAM Role ARN: $(terraform output -raw iam_role_arn 2>/dev/null)"
        echo "  Region: $(terraform output -raw bucket_region 2>/dev/null)"
    else
        echo "  Service Account: $(terraform output -raw service_account_email 2>/dev/null)"
        echo "  Location: $(terraform output -raw bucket_location 2>/dev/null)"
    fi
}

# Main
main() {
    check_prerequisites

    local provider="${1:-}"
    local region_or_project="${2:-}"

    if [ -z "$provider" ]; then
        echo -e "${YELLOW}Select cloud provider:${NC}"
        echo "  1) AWS S3"
        echo "  2) Google Cloud Storage (GCS)"
        echo -n "Enter choice [1 or 2]: "
        read -r choice

        case $choice in
            1) provider="s3" ;;
            2) provider="gcs" ;;
            *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
        esac
    fi

    validate_provider "$provider"

    if [ "$provider" = "s3" ]; then
        setup_s3 "$region_or_project"
    else
        setup_gcs "$region_or_project"
    fi

    deploy

    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Copy the environment variables above"
    echo "2. Add them to your cloud deployment platform (Streamlit Cloud, Heroku, Railway, etc.)"
    echo "3. For AWS: Create and add AWS credentials to your platform secrets"
    echo "4. For GCS: Create and add GCP service account key to your platform secrets"
    echo "5. Deploy your app and test settings persistence"
    echo ""
    echo -e "${BLUE}For detailed instructions, see: SETTINGS_PERSISTENCE_GUIDE.md${NC}"
}

main "$@"
