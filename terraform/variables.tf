# variables.tf - Root variables definition file

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "baby-mlops"  # From your .env
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"  # From your .env
}

variable "environment" {
  description = "The deployment environment (dev or prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "bucket_name" {
  description = "The GCS bucket for storing pipeline artifacts"
  type        = string
  default     = "baby-mlops-pipeline-bucket"  # From your .env
}

variable "appname" {
  description = "The application name"
  type        = string
  default     = "babyweight-pipeline-2025-py"  # From your .env
}

variable "service_account_email" {
  description = "The service account email for the pipeline"
  type        = string
  default     = "baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com"  # From your .env
}

variable "endpoint_display_name" {
  description = "The display name for the Vertex AI endpoint"
  type        = string
  default     = "baby-mlops-pipeline-endpoint"  # From your .env
}

variable "deploy_machine_type" {
  description = "The machine type for model deployment"
  type        = string
  default     = "n1-standard-2"  # From your .env
}

variable "deploy_min_replica_count" {
  description = "The minimum number of replicas for the deployed model"
  type        = number
  default     = 1  # From your .env
}

variable "deploy_max_replica_count" {
  description = "The maximum number of replicas for the deployed model"
  type        = number
  default     = 1  # From your .env
} 