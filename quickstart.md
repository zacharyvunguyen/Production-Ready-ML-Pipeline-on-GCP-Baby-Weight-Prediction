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

This dataset will be used for staging intermediate data tables. Ensure the location matches the `BQ_LOCATION` in your `.env` file (typically `US` for compatibility with the `bigquery-public-data.samples.natality` table).

```bash
bq --location=US mk --dataset --project_id=baby-mlops --description 'Staging dataset for baby MLOps pipeline' baby_mlops_data_staging
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

# BQML Model Configuration (Defaults shown, customize as needed)
BQML_MODEL_NAME="my_babyweight_model"
BQML_MODEL_VERSION_ALIASES="v1"
VAR_TARGET="weight_pounds"

# AutoML Model Configuration
VERTEX_DATASET_DISPLAY_NAME="baby-mlops-vertex-dataset"
AUTOML_MODEL_DISPLAY_NAME="baby-mlops-automl-model" 
AUTOML_BUDGET_MILLI_NODE_HOURS="1000"

# Deployment Configuration
ENDPOINT_DISPLAY_NAME="baby-mlops-endpoint"
DEPLOY_MACHINE_TYPE="n1-standard-2"
DEPLOY_MIN_REPLICA_COUNT="1"
DEPLOY_MAX_REPLICA_COUNT="1"
```

## 4. Running the ML Pipeline

You can run the modernized pipeline with both BQML and AutoML training, model selection, and deployment using the following commands:

### a. Compile the Pipeline Only

This will create the pipeline JSON specification without running it:

```bash
conda activate baby
python run_modernized_pipeline.py --compile-only
```

The compiled pipeline JSON will be saved in the `compiled_pipeline_specs` directory.

### b. Compile and Run the Pipeline

This will compile and execute the pipeline on Vertex AI:

```bash
conda activate baby
python run_modernized_pipeline.py --run-pipeline
```

You can monitor the pipeline execution in the Vertex AI Pipelines section of the Google Cloud Console. The pipeline includes:
- Data extraction and preprocessing
- BQML model training
- AutoML model training
- Model evaluation and selection
- Endpoint creation and model deployment

## 5. Running the Streamlit Application

The Streamlit application provides a user-friendly interface to interact with your deployed model.

### a. Make Sure Google Authentication is Set Up

Ensure you're authenticated with Google Cloud:

```bash
gcloud auth application-default login
```

### b. Launch the Streamlit App

```bash
conda activate baby
streamlit run streamlit_app_dynamic.py
```

The app will open in your default web browser (typically at http://localhost:8501) and allow you to:
- Select a deployed endpoint
- Enter pregnancy data
- Get baby weight predictions
- Visualize risk factors
- Compare predictions with different units (pounds, kilograms, etc.)

## 6. Project Structure Overview

- `src/pipeline_2025/`: Contains the pipeline component modules
- `compiled_pipeline_specs/`: Stores compiled pipeline JSON specifications
- `run_modernized_pipeline.py`: Main script to compile and run the pipeline
- `streamlit_app_dynamic.py`: Modern Streamlit application with enhanced visualization
- `.env`: Configuration file for project settings
- `requirements.txt`: Python package dependencies 