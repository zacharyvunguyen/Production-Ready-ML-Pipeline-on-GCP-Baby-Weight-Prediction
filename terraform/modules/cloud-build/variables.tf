# Cloud Build Module - variables.tf

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for Cloud Build"
  type        = string
}

variable "repository_id" {
  description = "The ID for the Artifact Registry repository"
  type        = string
  default     = "baby-weight-predictor"
}

variable "trigger_name" {
  description = "The name for the Cloud Build trigger"
  type        = string
  default     = "baby-weight-predictor-build"
}

variable "github_owner" {
  description = "The GitHub repository owner"
  type        = string
  default     = "zacharyvunguyen"  # Update with your GitHub username
}

variable "github_repo" {
  description = "The GitHub repository name"
  type        = string
  default     = "Production-Ready-ML-Pipeline-on-GCP-Baby-Weight-Prediction"
}

variable "cloud_run_service_name" {
  description = "The name of the Cloud Run service to deploy to"
  type        = string
  default     = "baby-weight-predictor"
} 