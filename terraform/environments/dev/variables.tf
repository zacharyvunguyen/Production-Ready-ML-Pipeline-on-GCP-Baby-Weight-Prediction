# Dev Environment - variables.tf

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
}

variable "bucket_name" {
  description = "The GCS bucket for storing pipeline artifacts"
  type        = string
}

variable "appname" {
  description = "The application name"
  type        = string
}

variable "service_account_email" {
  description = "The service account email for the pipeline"
  type        = string
} 