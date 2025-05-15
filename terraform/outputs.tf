# outputs.tf - Root outputs definition file

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region for resources"
  value       = var.region
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}

# IAM outputs
output "service_account_email" {
  description = "The service account email for the pipeline"
  value       = var.service_account_email
}

# These will be populated once the respective modules are implemented
output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = module.environment.cloud_run_service_url
  sensitive   = false
}

output "cloud_build_trigger_id" {
  description = "The ID of the created Cloud Build trigger"
  value       = module.environment.cloud_build_trigger_id
  sensitive   = false
} 