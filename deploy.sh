#!/bin/bash
# Deploy to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Exam Helper - Cloud Run Deployment ===${NC}\n"

# Get project ID (from argument or prompt)
if [ -z "$1" ]; then
    echo -e "${YELLOW}Enter your Google Cloud Project ID:${NC}"
    read PROJECT_ID
else
    PROJECT_ID=$1
fi

# Get region (from argument or use default)
if [ -z "$2" ]; then
    REGION="us-central1"
    echo -e "${YELLOW}Using default region: ${REGION}${NC}"
else
    REGION=$2
fi

echo -e "\n${GREEN}Project ID:${NC} $PROJECT_ID"
echo -e "${GREEN}Region:${NC} $REGION\n"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting active project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "\n${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet

# Set region
echo -e "\n${YELLOW}Setting region...${NC}"
gcloud config set run/region $REGION

# Deploy to Cloud Run
echo -e "\n${GREEN}Deploying to Cloud Run...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}\n"

gcloud run deploy exam-helper \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10 \
  --timeout=300 \
  --quiet

# Get service URL
echo -e "\n${GREEN}Deployment complete!${NC}"
SERVICE_URL=$(gcloud run services describe exam-helper --region=$REGION --format='value(status.url)')
echo -e "\n${GREEN}Your app is live at:${NC}"
echo -e "${GREEN}${SERVICE_URL}${NC}\n"

echo -e "${YELLOW}To view logs:${NC}"
echo "gcloud run services logs read exam-helper --region=$REGION"
echo -e "\n${YELLOW}To delete the service:${NC}"
echo "gcloud run services delete exam-helper --region=$REGION"
