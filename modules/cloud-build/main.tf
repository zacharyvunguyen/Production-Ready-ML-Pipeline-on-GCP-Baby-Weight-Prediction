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
      older_than = "2592000s"  # 30 days in seconds (30 * 24 * 60 * 60 seconds)
      tag_state  = "ANY"
    }
  }
} 