#!/bin/bash
# Script to create a simple monitoring dashboard for the Baby Weight Predictor

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided in environment
PROJECT_ID=${PROJECT:-"baby-mlops"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"baby-weight-predictor"}

echo "Creating monitoring dashboard for Cloud Run service: ${SERVICE_NAME}"

# Create dashboard JSON
cat << EOF > dashboard.json
{
  "displayName": "${SERVICE_NAME} Monitoring Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "xPos": 0,
        "yPos": 0,
        "widget": {
          "title": "Request Count",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type = \\"cloud_run_revision\\" AND resource.labels.service_name = \\"${SERVICE_NAME}\\" AND metric.type = \\"run.googleapis.com/request_count\\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM"
                    }
                  },
                  "unitOverride": "1"
                },
                "plotType": "LINE",
                "legendTemplate": "Request Count"
              }
            ],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Request Count",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "yPos": 0,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type = \\"cloud_run_revision\\" AND resource.labels.service_name = \\"${SERVICE_NAME}\\" AND metric.type = \\"run.googleapis.com/request_count\\" AND metric.labels.response_code_class = \\"4xx\\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM"
                    }
                  }
                },
                "plotType": "LINE",
                "legendTemplate": "4xx Errors"
              }
            ],
            "yAxis": {
              "label": "Error Rate",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 0,
        "yPos": 4,
        "widget": {
          "title": "Response Latency",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type = \\"cloud_run_revision\\" AND resource.labels.service_name = \\"${SERVICE_NAME}\\" AND metric.type = \\"run.googleapis.com/request_latencies\\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_PERCENTILE_99",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  },
                  "unitOverride": "ms"
                },
                "plotType": "LINE",
                "legendTemplate": "p99 Latency"
              }
            ],
            "yAxis": {
              "label": "Latency (ms)",
              "scale": "LINEAR"
            }
          }
        }
      }
    ]
  }
}
EOF

# Create the dashboard using gcloud
echo "Creating dashboard using gcloud..."
gcloud monitoring dashboards create --project=${PROJECT_ID} --config-from-file=dashboard.json

# Clean up
rm -f dashboard.json

echo "✅ Dashboard created successfully! View it at:"
echo "https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}" 