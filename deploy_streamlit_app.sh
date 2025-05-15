#!/bin/bash
# Script to deploy the Streamlit app to Cloud Run

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided in environment
PROJECT_ID=${PROJECT:-"baby-mlops"}
REGION=${REGION:-"us-central1"}
REPOSITORY=${REPOSITORY:-"babyweight-pipeline-2025-py-repo-dev"}
IMAGE_NAME=${IMAGE_NAME:-"baby-weight-predictor"}
TAG=${TAG:-"latest"}
SERVICE_NAME=${SERVICE_NAME:-"baby-weight-predictor"}
MIN_INSTANCES=${MIN_INSTANCES:-0}
MAX_INSTANCES=${MAX_INSTANCES:-2}
CPU=${CPU:-1}
MEMORY=${MEMORY:-"512Mi"}

# Full image path
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "Deploying Streamlit app to Cloud Run..."
echo "Service: ${SERVICE_NAME}"
echo "Image: ${IMAGE_PATH}"
echo "Region: ${REGION}"

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_PATH} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --min-instances=${MIN_INSTANCES} \
    --max-instances=${MAX_INSTANCES} \
    --cpu=${CPU} \
    --memory=${MEMORY} \
    --set-env-vars="PROJECT=${PROJECT_ID},REGION=${REGION}" \
    --service-account=${SERVICE_ACCOUNT}

# Get the deployed URL
URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo "✅ Deployment complete!"
echo "Your Streamlit app is available at: ${URL}" 