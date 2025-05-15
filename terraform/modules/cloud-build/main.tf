# Cloud Build Module - main.tf

# Create Artifact Registry repository for storing Docker images
resource "google_artifact_registry_repository" "app_repo" {
  provider      = google-beta
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "Docker repository for the Baby Weight Prediction application"
  
  # Configure cleanup policies to avoid storing too many old images
  cleanup_policy_dry_run = false
  
  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }
  
  cleanup_policies {
    id     = "delete-old-versions"
    action = "DELETE"
    condition {
      older_than = "2592000s" # 30 days in seconds
      tag_state  = "ANY"
    }
  }
}

# Create a Cloud Build trigger for the main branch
resource "google_cloudbuild_trigger" "main_branch_trigger" {
  name        = "${var.trigger_name}-main"
  description = "Build and deploy the Baby Weight Prediction app from the main branch"
  
  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }
  
  # Use the included Cloud Build configuration file
  included_files = ["Dockerfile", "streamlit_app_dynamic.py", "requirements.txt"]
  
  # Use a Cloud Build configuration file from the repository
  filename = "cloudbuild.yaml"
  
  # Substitution variables for the build
  substitutions = {
    _REGION        = var.region
    _REPOSITORY    = var.repository_id
    _SERVICE_NAME  = var.cloud_run_service_name
    _ARTIFACT_REPO = google_artifact_registry_repository.app_repo.repository_id
  }
}

# Create a Cloud Build trigger for the development branch
resource "google_cloudbuild_trigger" "dev_branch_trigger" {
  name        = "${var.trigger_name}-dev"
  description = "Build and deploy the Baby Weight Prediction app from the development branch"
  
  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^development$"
    }
  }
  
  # Use the included Cloud Build configuration file
  included_files = ["Dockerfile", "streamlit_app_dynamic.py", "requirements.txt"]
  
  # Use a Cloud Build configuration file from the repository
  filename = "cloudbuild-dev.yaml"
  
  # Substitution variables for the build
  substitutions = {
    _REGION        = var.region
    _REPOSITORY    = var.repository_id
    _SERVICE_NAME  = "${var.cloud_run_service_name}-dev"
    _ARTIFACT_REPO = google_artifact_registry_repository.app_repo.repository_id
  }
} 