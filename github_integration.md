# GitHub Integration with Cloud Build

This document provides step-by-step instructions for connecting your GitHub repository to Google Cloud Build.

## Prerequisites

- Google Cloud project with Cloud Build API enabled
- GitHub repository with your application code
- Owner or Admin access to the GitHub repository
- Appropriate IAM permissions in your GCP project

## Steps to Connect GitHub to Cloud Build

### 1. Navigate to Cloud Build in GCP Console

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `baby-mlops`
3. Navigate to **Cloud Build** > **Triggers**

### 2. Connect Your GitHub Repository

1. Click on **Connect Repository**
2. Select **GitHub (Cloud Build GitHub App)** as the source
3. Click **Continue**
4. If this is your first time connecting, you'll be prompted to install the Google Cloud Build GitHub app
5. Click **Install Google Cloud Build** to proceed to GitHub
6. Select the account where your repository is located
7. Choose whether to give access to all repositories or just select repositories
8. If selecting specific repositories, choose `Production-Ready-ML-Pipeline-on-GCP-Baby-Weight-Prediction`
9. Click **Install**
10. You'll be redirected back to GCP Console

### 3. Create Cloud Build Triggers

#### Main Branch Trigger

1. Click **Create Trigger**
2. Fill in the following details:
   - **Name**: `babyweight-pipeline-2025-py-trigger-main`
   - **Description**: `Build and deploy the Baby Weight Prediction app from the main branch`
   - **Event**: `Push to a branch`
   - **Repository**: Your connected repository
   - **Branch**: `^main$` (regex for exact match)
   - **Configuration**: `Cloud Build configuration file (yaml or json)`
   - **Location**: `Repository`
   - **Cloud Build configuration file location**: `cloudbuild.yaml`
3. Under **Substitution variables**, add the following:
   - `_REGION`: `us-central1`
   - `_REPOSITORY`: `babyweight-pipeline-2025-py-repo-dev`
   - `_SERVICE_NAME`: `baby-weight-predictor`
   - `_ARTIFACT_REPO`: `babyweight-pipeline-2025-py-repo-dev`
4. Click **Create**

#### Development Branch Trigger

1. Click **Create Trigger**
2. Fill in the following details:
   - **Name**: `babyweight-pipeline-2025-py-trigger-dev`
   - **Description**: `Build and deploy the Baby Weight Prediction app from the development branch`
   - **Event**: `Push to a branch`
   - **Repository**: Your connected repository
   - **Branch**: `^development$` (regex for exact match)
   - **Configuration**: `Cloud Build configuration file (yaml or json)`
   - **Location**: `Repository`
   - **Cloud Build configuration file location**: `cloudbuild-dev.yaml`
3. Under **Substitution variables**, add the following:
   - `_REGION`: `us-central1`
   - `_REPOSITORY`: `babyweight-pipeline-2025-py-repo-dev`
   - `_SERVICE_NAME`: `baby-weight-predictor-dev`
   - `_ARTIFACT_REPO`: `babyweight-pipeline-2025-py-repo-dev`
4. Click **Create**

### 4. Test the Integration

1. Create a new branch or push changes to an existing branch
2. Monitor the build progress in the Cloud Build console
3. Verify that the application is deployed to Cloud Run

## Troubleshooting

- **Build fails**: Check the Cloud Build logs for errors
- **Permission issues**: Ensure the Cloud Build service account has necessary permissions
- **Trigger not firing**: Verify the branch regex pattern matches your branch name

## Next Steps

After successful integration:

1. Set up branch protection rules in GitHub
2. Configure build notifications
3. Add build status badges to your README.md 