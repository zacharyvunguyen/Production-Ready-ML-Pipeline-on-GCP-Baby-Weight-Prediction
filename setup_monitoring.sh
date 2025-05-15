#!/bin/bash
# Script to set up monitoring for the Baby Weight Predictor Cloud Run service

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided in environment
PROJECT_ID=${PROJECT:-"baby-mlops"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"baby-weight-predictor"}
NOTIFICATION_CHANNELS=""

echo "Setting up monitoring for Cloud Run service: ${SERVICE_NAME}"

# Create uptime check for the Cloud Run service
echo "Creating uptime check..."
gcloud monitoring uptime-check create http \
    --display-name="${SERVICE_NAME}-uptime" \
    --uri="https://${SERVICE_NAME}-e6n3dplaoq-uc.a.run.app" \
    --path="/" \
    --check-interval=60s \
    --timeout=10s \
    --project=${PROJECT_ID}

# Create alert policy for error rate
echo "Creating error rate alert policy..."
cat << EOF > error_rate_policy.json
{
  "displayName": "${SERVICE_NAME} Error Rate Alert",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Error Rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${SERVICE_NAME}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "0s",
        "trigger": {
          "count": 1
        }
      }
    }
  ]
}
EOF

gcloud monitoring alerts create \
    --project=${PROJECT_ID} \
    --notification-channels=${NOTIFICATION_CHANNELS} \
    --policy-from-file=error_rate_policy.json

# Create alert policy for latency
echo "Creating latency alert policy..."
cat << EOF > latency_policy.json
{
  "displayName": "${SERVICE_NAME} Latency Alert",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Latency > 2s",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${SERVICE_NAME}\" AND metric.type = \"run.googleapis.com/request_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_PERCENTILE_99",
            "crossSeriesReducer": "REDUCE_MEAN"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 2000,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ]
}
EOF

gcloud monitoring alerts create \
    --project=${PROJECT_ID} \
    --notification-channels=${NOTIFICATION_CHANNELS} \
    --policy-from-file=latency_policy.json

# Clean up temporary files
rm -f error_rate_policy.json latency_policy.json

echo "✅ Monitoring setup complete!"
echo "You can view your monitoring dashboard at: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo "To create notification channels for alerts, visit: https://console.cloud.google.com/monitoring/alerting/notifications?project=${PROJECT_ID}" 