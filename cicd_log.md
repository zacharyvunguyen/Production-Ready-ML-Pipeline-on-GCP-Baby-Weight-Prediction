# CI/CD Implementation Log

## 2024-05-14: Phase 1 - Infrastructure as Code

### Resources Validated (terraform plan)

#### IAM Permissions (4)
- Cloud Run Invoker role for service account
- Vertex AI User role for service account
- Cloud Build Builder role for service account
- Artifact Registry Writer role for service account

#### Artifact Registry (1)
- Docker repository for application images
- Cleanup policies: keep 5 most recent, delete older than 30 days

#### Cloud Build Triggers (2)
- Main branch trigger (cloudbuild.yaml)
- Development branch trigger (cloudbuild-dev.yaml)
- Both monitoring GitHub repository changes

#### Cloud Run Services (2)
- Streamlit application deployment service
- IAM policy for public access

### Outcomes
- ✅ Terraform initialization successful
- ✅ Configuration validated with plan
- ✅ Resources applied to GCP
- ✅ Artifact Registry repository created: babyweight-pipeline-2025-py-repo-dev
- ✅ Cloud Run service deployed: https://babyweight-pipeline-2025-py-dev-e6n3dplaoq-uc.a.run.app
- ❌ Cloud Build triggers not created (GitHub integration pending)

### Current Status
- Infrastructure is ~70% complete
- Cloud Run service is running with a placeholder container
- Artifact Registry repository is set up with cleanup policies
- IAM permissions are configured for the service account
- GitHub repository not yet connected to Cloud Build

## 2024-05-15: Phase 2 - GitHub Integration & Deployment

### Actions Completed
- ✅ Created build_and_push.sh script for Docker image building
- ✅ Created deploy_streamlit_app.sh script for Cloud Run deployment
- ✅ Added CI/CD variables to .env file
- ✅ Built and pushed Docker image to Artifact Registry
- ✅ Deployed Streamlit app to Cloud Run
- ✅ Application successfully deployed at: https://baby-weight-predictor-e6n3dplaoq-uc.a.run.app

### Current Status
- Manual deployment pipeline working successfully
- Streamlit app deployed and accessible
- Docker image stored in Artifact Registry with v1 tag
- Environment variables configured for CI/CD

### Next Actions
- Connect GitHub repository to Cloud Build in GCP Console
- Create GitHub repository connection
- Manually create Cloud Build triggers
- Test automated deployment pipeline with a code change 