# Dev Environment - main.tf

# Configure the Cloud Run service
module "cloud_run" {
  source = "../../modules/cloud-run"
  
  project_id           = var.project_id
  region               = var.region
  service_name         = "${var.appname}-dev"
  service_account_email = var.service_account_email
  
  # Development-specific settings
  min_instances        = 0
  max_instances        = 1
  cpu                  = "1"
  memory               = "512Mi"
  
  # Environment variables for the application
  environment_variables = {
    "ENV"              = "development"
    "BUCKET"           = var.bucket_name
    "BQ_LOCATION"      = "US"
    "BQ_DATASET_STAGING" = "baby_mlops_data_staging"
  }
}

# Configure the Cloud Build triggers
module "cloud_build" {
  source = "../../modules/cloud-build"
  
  project_id           = var.project_id
  region               = var.region
  repository_id        = "${var.appname}-repo-dev"
  trigger_name         = "${var.appname}-trigger"
  cloud_run_service_name = module.cloud_run.service_name
  
  # GitHub repository settings
  github_owner         = "zacharyvunguyen"  # Update with your GitHub username
  github_repo          = "Production-Ready-ML-Pipeline-on-GCP-Baby-Weight-Prediction"
} 