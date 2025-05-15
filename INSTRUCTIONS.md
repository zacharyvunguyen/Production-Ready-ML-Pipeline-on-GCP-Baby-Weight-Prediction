# Instructions: Baby Weight Prediction MLOps Project

This document provides step-by-step instructions to recreate the Production-Ready ML Pipeline for Baby Weight Prediction on GCP.

## Prerequisites

* Google Cloud Platform account
* Python 3.10+
* Google Cloud SDK installed and configured
* Terraform installed
* Docker installed
* Git installed

## Phase 1: Infrastructure Setup with Terraform

1. **Clone the repository**:
   * `git clone https://github.com/your-username/Production-Ready-ML-Pipeline-on-GCP-Baby-Weight-Prediction.git`
   * `cd Production-Ready-ML-Pipeline-on-GCP-Baby-Weight-Prediction`

2. **Configure environment variables**:
   * Copy `deployment.env.example` to `.env`
   * Update with your GCP PROJECT, REGION, and other required values

3. **Initialize and apply Terraform**:
   * `cd terraform`
   * `terraform init`
   * For development environment: 
     * `cd environments/dev`
     * `terraform plan -out=tfplan`
     * `terraform apply "tfplan"`
   * For production environment:
     * `cd environments/prod`
     * `terraform plan -out=tfplan`
     * `terraform apply "tfplan"`

## Phase 2: ML Pipeline Implementation

1. **Create the Vertex AI Pipeline**:
   * Run the notebook: `00_ml_pipeline.ipynb`
   * Alternatively, execute the pipeline script: `python run_modernized_pipeline.py`

2. **Configure pipeline components**:
   * Check paths and parameters in `src/pipeline_2025/*.py` files
   * Ensure BigQuery dataset and table access is configured

3. **Run the pipeline**:
   * Execute `python run_modernized_pipeline.py` to build and run the pipeline
   * This will:
     * Extract data from BigQuery's natality dataset
     * Preprocess the data for model training
     * Train parallel BQML and AutoML models
     * Evaluate and compare model performance
     * Select the best model based on metrics
     * Register the model in Vertex AI Model Registry
     * Deploy the model to an endpoint

## Phase 3: Containerization and Application Development

1. **Build the Streamlit application**:
   * Review and update `streamlit_app_dynamic.py`
   * Test locally with `streamlit run streamlit_app_dynamic.py`

2. **Build and push Docker image**:
   * Update Dockerfile if needed
   * Run `./build_and_push.sh` to build and push to Artifact Registry
   * Alternatively, manually:
     * `docker build -t REGION-docker.pkg.dev/PROJECT/REPO/baby-weight-predictor:TAG .`
     * `docker push REGION-docker.pkg.dev/PROJECT/REPO/baby-weight-predictor:TAG`

3. **Deploy to Cloud Run**:
   * Run `./deploy_streamlit_app.sh` to deploy
   * Alternatively, manually:
     * `gcloud run deploy baby-weight-predictor --image=REGION-docker.pkg.dev/PROJECT/REPO/baby-weight-predictor:TAG --region=REGION`

## Phase 4: CI/CD Pipeline Setup

1. **Connect GitHub repository**:
   * Follow instructions in `github_integration.md` to connect your GitHub repo to Cloud Build

2. **Configure Cloud Build triggers**:
   * Verify `cloudbuild.yaml` and `cloudbuild-dev.yaml` configurations
   * Use GCP Console to set up and test triggers
   * Link triggers to main and development branches

3. **Test the CI/CD pipeline**:
   * Make a small change to your development branch and push
   * Verify Cloud Build automatically builds and deploys

## Phase 5: Monitoring Setup

1. **Set up Cloud Monitoring**:
   * Run `./setup_monitoring.sh` to configure basic monitoring
   * Run `./create_simple_dashboard.sh` to create a custom dashboard

2. **Generate test traffic**:
   * Send requests to your Cloud Run endpoints to validate monitoring
   * Check dashboard to verify metrics are being collected

3. **Configure alerting**:
   * Set up appropriate alerts for error rates and latency
   * Configure notification channels

## Maintenance and Extension

* **Update models**: Run the pipeline periodically to train on new data
* **Monitor performance**: Check dashboard regularly for performance issues
* **Extend features**: Add new features to the Streamlit app as needed
* **Scale resources**: Adjust autoscaling parameters as traffic grows

## Troubleshooting

* **Check logs**: Use Cloud Logging to debug issues
* **Verify permissions**: Most issues are related to IAM permissions
* **Check quotas**: Ensure you haven't exceeded GCP quotas 