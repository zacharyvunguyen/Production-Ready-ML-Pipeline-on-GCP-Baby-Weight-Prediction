# IAM Module - main.tf

# Note: We'll use the existing service account that you've already created
# Instead of creating a new one, we'll grant it the necessary permissions

# Grant the service account permission to invoke Cloud Run services
resource "google_project_iam_member" "cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${var.service_account_email}"
}

# Grant the service account permission to access the Vertex AI endpoints
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${var.service_account_email}"
}

# Grant the service account permission to run Cloud Build jobs
resource "google_project_iam_member" "cloud_build_user" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${var.service_account_email}"
}

# Grant the service account permission to push and pull from Artifact Registry
resource "google_project_iam_member" "artifact_registry_user" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${var.service_account_email}"
} 