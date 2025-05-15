#!/bin/bash
# Script to build and push the Docker image to Artifact Registry

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

# Full image path
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "Building Docker image: ${IMAGE_PATH}"
docker build -t ${IMAGE_PATH} .

# Configure Docker to use Google Cloud credentials
echo "Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo "Pushing Docker image to Artifact Registry..."
docker push ${IMAGE_PATH}

echo "Image successfully built and pushed to: ${IMAGE_PATH}"
echo "You can deploy this image to Cloud Run with:"
echo "gcloud run deploy ${IMAGE_NAME} --image=${IMAGE_PATH} --platform=managed --region=${REGION} --allow-unauthenticated" 