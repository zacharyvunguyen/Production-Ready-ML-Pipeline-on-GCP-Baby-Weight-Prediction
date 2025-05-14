# Cloud Run Module - outputs.tf

output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.streamlit_app.status[0].url
}

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_service.streamlit_app.name
}

output "service_location" {
  description = "The location of the Cloud Run service"
  value       = google_cloud_run_service.streamlit_app.location
} 