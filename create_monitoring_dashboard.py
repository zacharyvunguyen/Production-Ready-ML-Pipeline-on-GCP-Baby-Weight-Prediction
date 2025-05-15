#!/usr/bin/env python3
"""
Create a basic monitoring dashboard for the Baby Weight Predictor Cloud Run service.
This script uses the Google Cloud Monitoring API to create a dashboard with
key metrics for the Cloud Run service.
"""

import os
import json
from google.cloud import monitoring_dashboard_v1
from google.protobuf import json_format

# Load environment variables from .env file if it exists
env_vars = {}
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value

# Set default values if not provided in environment
PROJECT_ID = env_vars.get('PROJECT', 'baby-mlops')
SERVICE_NAME = env_vars.get('SERVICE_NAME', 'baby-weight-predictor')
REGION = env_vars.get('REGION', 'us-central1')

print(f"Creating monitoring dashboard for service: {SERVICE_NAME} in project: {PROJECT_ID}")

# Initialize the dashboard client
client = monitoring_dashboard_v1.DashboardsServiceClient()

# Define the dashboard JSON
dashboard_json = {
    "displayName": f"{SERVICE_NAME} Monitoring Dashboard",
    "mosaicLayout": {
        "columns": 12,
        "tiles": [
            {
                "width": 6,
                "height": 4,
                "widget": {
                    "title": "Request Count",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": f'resource.type = "cloud_run_revision" AND resource.labels.service_name = "{SERVICE_NAME}" AND metric.type = "run.googleapis.com/request_count"',
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
                "widget": {
                    "title": "Response Latency",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": f'resource.type = "cloud_run_revision" AND resource.labels.service_name = "{SERVICE_NAME}" AND metric.type = "run.googleapis.com/request_latencies"',
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
            },
            {
                "width": 6,
                "height": 4,
                "yPos": 4,
                "widget": {
                    "title": "Instance Count",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": f'resource.type = "cloud_run_revision" AND resource.labels.service_name = "{SERVICE_NAME}" AND metric.type = "run.googleapis.com/container/instance_count"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MAX",
                                            "crossSeriesReducer": "REDUCE_SUM"
                                        }
                                    },
                                    "unitOverride": "1"
                                },
                                "plotType": "LINE",
                                "legendTemplate": "Instance Count"
                            }
                        ],
                        "yAxis": {
                            "label": "Instances",
                            "scale": "LINEAR"
                        }
                    }
                }
            },
            {
                "width": 6,
                "height": 4,
                "xPos": 6,
                "yPos": 4,
                "widget": {
                    "title": "Error Count",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": f'resource.type = "cloud_run_revision" AND resource.labels.service_name = "{SERVICE_NAME}" AND metric.type = "run.googleapis.com/request_count" AND metric.labels.response_code_class = "4xx"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE",
                                            "crossSeriesReducer": "REDUCE_SUM"
                                        }
                                    },
                                    "unitOverride": "1"
                                },
                                "plotType": "LINE",
                                "legendTemplate": "4xx Errors"
                            },
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": f'resource.type = "cloud_run_revision" AND resource.labels.service_name = "{SERVICE_NAME}" AND metric.type = "run.googleapis.com/request_count" AND metric.labels.response_code_class = "5xx"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE",
                                            "crossSeriesReducer": "REDUCE_SUM"
                                        }
                                    },
                                    "unitOverride": "1"
                                },
                                "plotType": "LINE",
                                "legendTemplate": "5xx Errors"
                            }
                        ],
                        "timeshiftDuration": "0s",
                        "yAxis": {
                            "label": "Error Count",
                            "scale": "LINEAR"
                        }
                    }
                }
            }
        ]
    }
}

# Convert the JSON to proto
dashboard = json_format.ParseDict(
    dashboard_json, monitoring_dashboard_v1.Dashboard()
)

# Create the dashboard
parent = f"projects/{PROJECT_ID}"
try:
    response = client.create_dashboard(parent=parent, dashboard=dashboard)
    print(f"✅ Dashboard created successfully! View it at:")
    print(f"https://console.cloud.google.com/monitoring/dashboards?project={PROJECT_ID}")
except Exception as e:
    print(f"❌ Error creating dashboard: {e}") 