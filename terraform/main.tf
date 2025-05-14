# main.tf - Root Terraform configuration file

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
  
  # Backend configuration will be set up in a separate file
  # backend "gcs" {}
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Import environment-specific modules
module "environment" {
  source = "./environments/dev"
  
  project_id = var.project_id
  region     = var.region
  bucket_name = var.bucket_name
  appname    = var.appname
  service_account_email = var.service_account_email
}

# Common modules that apply to all environments
module "iam" {
  source = "./modules/iam"
  
  project_id = var.project_id
  service_account_email = var.service_account_email
} 