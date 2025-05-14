# IAM Module - variables.tf

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "service_account_email" {
  description = "The service account email to use for the pipeline"
  type        = string
} 