# Cloud Build Module - outputs.tf

output "main_trigger_id" {
  description = "The ID of the main branch Cloud Build trigger"
  value       = google_cloudbuild_trigger.main_branch_trigger.id
}

output "dev_trigger_id" {
  description = "The ID of the development branch Cloud Build trigger"
  value       = google_cloudbuild_trigger.dev_branch_trigger.id
}

output "artifact_registry_repository" {
  description = "The Artifact Registry repository name"
  value       = google_artifact_registry_repository.app_repo.name
} 