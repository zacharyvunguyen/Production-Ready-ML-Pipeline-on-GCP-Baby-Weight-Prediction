"""Kubeflow Pipeline (KFP) components for data extraction and preprocessing.

These components are designed to be used in a Vertex AI Pipeline and handle
the initial stages of an ML workflow:
1. Extracting relevant data from a source BigQuery table.
2. Preprocessing the extracted data, including feature engineering and
   creating data splits (TRAIN, VALIDATE, TEST).
"""
import logging
from typing import NamedTuple

from kfp import dsl

# Configure basic logging
logging.basicConfig(level=logging.INFO)


@dsl.component(
    base_image="python:3.10",  # Updated Python version
    packages_to_install=["google-cloud-bigquery>=3.0.0"],
)
def extract_source_data(
    project_id: str,
    source_bq_table_id: str,
    extracted_bq_table_id: str,
    filter_year: int,
    region: str,  # Though not directly used by BQ client for multi-region, good for consistency
) -> NamedTuple('outputs', [('extracted_table_uri', str), ('extracted_table_id', str)]):
    """Extracts and filters data from a source BigQuery table.

    Args:
        project_id: The GCP project ID.
        source_bq_table_id: Full ID of the source BigQuery table (e.g., project.dataset.table).
        extracted_bq_table_id: Full ID for the output BigQuery table for extracted data.
        filter_year: The year used to filter the data (e.g., data > filter_year).
        region: The GCP region where the pipeline is running (for consistency).

    Returns:
        NamedTuple with:
            extracted_table_uri: The URI of the newly created extracted table.
            extracted_table_id: The ID of the newly created extracted table.
    """
    import logging # Ensure logging is imported within the component function
    from google.cloud import bigquery
    import json
    from collections import namedtuple # Keep for instantiation

    # Basic configuration for logging within this component
    # This ensures logs from this component are formatted and have a level set.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info(f"Starting data extraction from {source_bq_table_id}")
    logging.info(f"Project ID: {project_id}, Output Table: {extracted_bq_table_id}")
    logging.info(f"Filtering data for year > {filter_year}")
    logging.info(f"Using region: {region} (should be US for public dataset access)")

    bq_client = bigquery.Client(project=project_id)

    # First ensure the dataset exists with US location
    dataset_id = extracted_bq_table_id.split('.')[1]  # Get the dataset name from the full table ID
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    
    try:
        # Try to get the dataset to check if it exists
        dataset = bq_client.get_dataset(dataset_ref)
        logging.info(f"Dataset {dataset_id} already exists with location: {dataset.location}")
        if dataset.location != "US":
            logging.warning(f"Dataset location is {dataset.location}, not US as required for public dataset access")
    except Exception as e:
        # Dataset doesn't exist, create it
        logging.info(f"Creating dataset {dataset_id} in US location")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"  # Set the location to US multi-region
        dataset = bq_client.create_dataset(dataset, exists_ok=True)
        logging.info(f"Dataset {dataset_id} created with location: {dataset.location}")

    query = f"""
    CREATE OR REPLACE TABLE `{extracted_bq_table_id}` AS (
    SELECT
        weight_pounds,
        is_male,
        mother_age,
        plurality,
        gestation_weeks,
        cigarette_use,
        alcohol_use,
        year,
        month,
        wday,
        state,
        mother_birth_state
    FROM
        `{source_bq_table_id}`
    WHERE
        year > {filter_year}
        AND weight_pounds > 0
        AND mother_age > 0
        AND plurality > 0
        AND gestation_weeks > 19
    );
    """

    logging.info("Executing BigQuery job for data extraction...")
    try:
        # Always use US location for the job to access public dataset
        logging.info(f"Explicitly setting job location to US for public dataset access")
        job_config = bigquery.QueryJobConfig()
        query_job = bq_client.query(query, job_config=job_config, location="US")
        query_job.result()  # Wait for the job to complete
        logging.info(
            f"Successfully extracted data to {extracted_bq_table_id}. Job ID: {query_job.job_id}"
        )
    except Exception as e:
        logging.error(f"BigQuery job failed: {e}")
        raise

    # Create output values
    extracted_table_uri_val = f"bq://{extracted_bq_table_id}"
    extracted_table_id_val = extracted_bq_table_id
    
    # Log the outputs for debugging
    logging.info(f"Output - extracted_table_uri: {extracted_table_uri_val}")
    logging.info(f"Output - extracted_table_id: {extracted_table_id_val}")
    
    # Instantiate the inline NamedTuple for return
    Outputs = namedtuple('outputs', ['extracted_table_uri', 'extracted_table_id'])
    return Outputs(extracted_table_uri=extracted_table_uri_val, extracted_table_id=extracted_table_id_val)


@dsl.component(
    base_image="python:3.10",  # Updated Python version
    packages_to_install=["google-cloud-bigquery>=3.0.0"],
)
def preprocess_data_and_split(
    project_id: str,
    input_bq_table_id: str,
    preprocessed_bq_table_id: str,
    data_limit: int,
    region: str,  # Though not directly used by BQ client, good for consistency
) -> NamedTuple('outputs', [('preprocessed_table_uri', str), ('preprocessed_table_id', str)]):
    """Preprocesses data and splits it into TRAIN, VALIDATE, and TEST sets.

    Args:
        project_id: The GCP project ID.
        input_bq_table_id: Full ID of the input BigQuery table to preprocess.
        preprocessed_bq_table_id: Full ID for the output BigQuery table for preprocessed data.
        data_limit: The maximum number of rows to process from the input table.
        region: The GCP region where the pipeline is running (for consistency).

    Returns:
        NamedTuple with:
            preprocessed_table_uri: URI of the newly created preprocessed table.
            preprocessed_table_id: ID of the newly created preprocessed table.
    """
    import logging # Ensure logging is imported within the component function
    from google.cloud import bigquery
    import json
    from collections import namedtuple # Keep for instantiation

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info(f"Starting data preprocessing for {input_bq_table_id}")
    logging.info(f"Project ID: {project_id}, Output Table: {preprocessed_bq_table_id}")
    logging.info(f"Applying data limit: {data_limit}")
    logging.info(f"Using region: {region}")

    bq_client = bigquery.Client(project=project_id)

    # First ensure the dataset exists with correct location
    dataset_id = preprocessed_bq_table_id.split('.')[1]  # Get the dataset name from the full table ID
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    
    try:
        # Try to get the dataset to check if it exists
        dataset = bq_client.get_dataset(dataset_ref)
        logging.info(f"Dataset {dataset_id} already exists with location: {dataset.location}")
    except Exception as e:
        # Dataset doesn't exist, create it
        logging.info(f"Creating dataset {dataset_id} with location {region}")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = region
        dataset = bq_client.create_dataset(dataset, exists_ok=True)
        logging.info(f"Dataset {dataset_id} created with location: {dataset.location}")

    query = f"""
    CREATE OR REPLACE TABLE `{preprocessed_bq_table_id}` AS (
        WITH all_hash_limit AS (
            SELECT
                weight_pounds,
                CAST(is_male AS STRING) AS is_male,
                mother_age,
                CASE
                    WHEN plurality = 1 THEN "Single(1)"
                    WHEN plurality = 2 THEN "Twins(2)"
                    WHEN plurality = 3 THEN "Triplets(3)"
                    WHEN plurality = 4 THEN "Quadruplets(4)"
                    WHEN plurality = 5 THEN "Quintuplets(5)"
                    ELSE CAST(plurality AS STRING)  -- Keep original if not in specific cases
                END AS plurality_category, -- Renamed for clarity
                gestation_weeks,
                IFNULL(CAST(cigarette_use AS STRING), "Unknown") AS cigarette_use_str,
                IFNULL(CAST(alcohol_use AS STRING), "Unknown") AS alcohol_use_str,
                -- Create a hash for reproducible splitting
                ABS(FARM_FINGERPRINT(
                    CONCAT(
                        CAST(year AS STRING),
                        CAST(month AS STRING),
                        CAST(COALESCE(wday, 0) AS STRING), -- Handle potential NULL wday
                        CAST(IFNULL(state, "Unknown") AS STRING),
                        CAST(IFNULL(mother_birth_state, "Unknown") AS STRING)
                    )
                )) AS hash_values
            FROM
                `{input_bq_table_id}`
            LIMIT {data_limit}
        )
        SELECT
            * EXCEPT(hash_values), -- Exclude the temporary hash column
            -- Create data splits (approx. 80% TRAIN, 10% VALIDATE, 10% TEST)
            CASE
                WHEN MOD(hash_values, 10) < 8 THEN "TRAIN"
                WHEN MOD(hash_values, 10) = 8 THEN "VALIDATE" -- Use = 8 for 10%
                ELSE "TEST"
            END AS data_split
        FROM all_hash_limit
    );
    """

    logging.info("Executing BigQuery job for data preprocessing and splitting...")
    try:
        # Use the same region as the input table's dataset
        input_dataset_id = input_bq_table_id.split('.')[1]
        input_dataset = bq_client.get_dataset(bigquery.DatasetReference(project_id, input_dataset_id))
        location = input_dataset.location
        logging.info(f"Using location {location} for preprocessing job (matches input dataset)")
        
        job_config = bigquery.QueryJobConfig()
        query_job = bq_client.query(query, location=location, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        logging.info(
            f"Successfully preprocessed data to {preprocessed_bq_table_id}. Job ID: {query_job.job_id}"
        )
    except Exception as e:
        logging.error(f"BigQuery job failed: {e}")
        raise

    # Create output values
    preprocessed_table_uri_val = f"bq://{preprocessed_bq_table_id}"
    preprocessed_table_id_val = preprocessed_bq_table_id
    
    # Log the outputs for debugging
    logging.info(f"Output - preprocessed_table_uri: {preprocessed_table_uri_val}")
    logging.info(f"Output - preprocessed_table_id: {preprocessed_table_id_val}")
    
    # Instantiate the inline NamedTuple for return
    Outputs = namedtuple('outputs', ['preprocessed_table_uri', 'preprocessed_table_id'])
    return Outputs(preprocessed_table_uri=preprocessed_table_uri_val, preprocessed_table_id=preprocessed_table_id_val)
