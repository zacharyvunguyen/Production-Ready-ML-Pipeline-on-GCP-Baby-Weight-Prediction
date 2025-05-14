# Dev Environment - outputs.tf

output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = module.cloud_run.service_url
}

output "cloud_build_trigger_id" {
  description = "The ID of the created Cloud Build trigger"
  value       = module.cloud_build.main_trigger_id
}

output "artifact_registry_repository" {
  description = "The Artifact Registry repository name"
  value       = module.cloud_build.artifact_registry_repository
} 