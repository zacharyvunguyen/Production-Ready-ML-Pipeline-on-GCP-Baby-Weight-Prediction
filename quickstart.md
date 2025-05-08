# Project Quickstart: Baby MLOps Pipeline

This document outlines the steps to set up the Google Cloud Platform (GCP) resources and the local Python environment for the Baby MLOps Pipeline project.

## 1. GCP Resource Setup

The following `gcloud` commands were used to provision the necessary infrastructure on GCP.

**Project ID:** `baby-mlops`
**Region:** `us-central1`

### a. Create GCS Bucket

This bucket will store pipeline artifacts.

```bash
gcloud storage buckets create gs://baby-mlops-pipeline-bucket --project=baby-mlops --location=us-central1 --uniform-bucket-level-access
```

### b. Create BigQuery Dataset

This dataset will be used for staging intermediate data tables.

```bash
bq --location=us-central1 mk --dataset --project_id=baby-mlops --description 'Staging dataset for baby MLOps pipeline' baby_mlops_data_staging
```

### c. Create Service Account

This service account will be used by Vertex AI Pipelines to interact with other GCP services.

```bash
gcloud iam service-accounts create baby-mlops-pipeline-runner --display-name='Baby MLOps Pipeline Runner' --project=baby-mlops
```
The created service account email is: `baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com`

### d. Grant Permissions to Service Account

The service account needs permissions for GCS, BigQuery, and Vertex AI.

```bash
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/storage.objectAdmin'
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/bigquery.dataEditor'
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/bigquery.jobUser'
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/aiplatform.user'
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/bigquery.dataViewer'
gcloud projects add-iam-policy-binding baby-mlops --member='serviceAccount:baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com' --role='roles/bigquery.user'
```

### e. Enable Vertex AI API

This API is required to run Vertex AI Pipelines and other Vertex AI services.

```bash
gcloud services enable aiplatform.googleapis.com --project=baby-mlops
```

## 2. Local Python Environment Setup

These commands set up a Conda environment with Python 3.10 and install the project dependencies.

```bash
conda create --name baby python=3.10 -y
conda activate baby
pip install -r requirements.txt
```

## 3. `.env` File Configuration

Ensure you have a `.env` file in the project root with the following (at a minimum):

```dotenv
# Core GCP Configuration
PROJECT="baby-mlops"
REGION="us-central1"
SERVICE_ACCOUNT="baby-mlops-pipeline-runner@baby-mlops.iam.gserviceaccount.com"
BUCKET="baby-mlops-pipeline-bucket"
BQ_LOCATION="US"

# Pipeline Application Configuration
APPNAME="baby-mlops-pipeline"
PIPELINE_ROOT="gs://baby-mlops-pipeline-bucket/pipeline_root/baby-mlops-pipeline"
ENABLE_CACHING="true"

# Data Configuration
SOURCE_BQ_TABLE="bigquery-public-data.samples.natality"
BQ_DATASET_STAGING="baby_mlops_data_staging"
EXTRACTED_DATA_TABLE_NAME="natality_source_extract"
PREPPED_DATA_TABLE_NAME="natality_features_prepped"
DATA_EXTRACTION_YEAR="2000"
DATA_PREPROCESSING_LIMIT="100000"
``` 