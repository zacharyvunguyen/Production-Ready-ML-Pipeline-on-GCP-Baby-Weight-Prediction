# Cloud Run Module - variables.tf

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run service"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "baby-weight-predictor"
}

variable "container_image" {
  description = "The Docker image to deploy (initially a placeholder)"
  type        = string
  default     = "gcr.io/cloudrun/hello:latest"  # Placeholder, will be replaced by Cloud Build
}

variable "service_account_email" {
  description = "The service account email for the Cloud Run service"
  type        = string
}

variable "cpu" {
  description = "The CPU allocation for the Cloud Run service"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "The memory allocation for the Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "The minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "The maximum number of instances"
  type        = number
  default     = 2
}

variable "container_concurrency" {
  description = "The maximum number of concurrent requests per container"
  type        = number
  default     = 80
}

variable "timeout_seconds" {
  description = "The request timeout in seconds"
  type        = number
  default     = 300
}

variable "environment_variables" {
  description = "Environment variables to set on the container"
  type        = map(string)
  default     = {}
} 