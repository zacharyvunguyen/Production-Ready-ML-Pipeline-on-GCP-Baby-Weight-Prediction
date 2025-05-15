# Cloud Run Module - main.tf

# Create Cloud Run service for the Streamlit app
resource "google_cloud_run_service" "streamlit_app" {
  name     = var.service_name
  location = var.region
  
  template {
    spec {
      containers {
        image = var.container_image
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
        
        # Environment variables for the application
        env {
          name  = "PROJECT"
          value = var.project_id
        }
        
        env {
          name  = "REGION"
          value = var.region
        }
        
        # Add other environment variables as needed
        dynamic "env" {
          for_each = var.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
      }
      
      # Use the service account for authentication
      service_account_name = var.service_account_email
      
      # Set the container concurrency
      container_concurrency = var.container_concurrency
      
      # Set the timeout
      timeout_seconds = var.timeout_seconds
    }
    
    # Configure autoscaling
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
      }
    }
  }
  
  # Metadata for the service
  metadata {
    annotations = {
      "run.googleapis.com/client-name" = "terraform"
    }
  }
  
  # Traffic configuration - 100% to latest revision
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  # Ignore changes to the image as it will be updated by Cloud Build
  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

# Make the Cloud Run service publicly accessible
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.streamlit_app.name
  location = google_cloud_run_service.streamlit_app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
} 