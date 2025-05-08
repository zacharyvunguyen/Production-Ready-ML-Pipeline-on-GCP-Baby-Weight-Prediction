import os
import json
import logging
from datetime import datetime
import argparse # For command-line arguments

from dotenv import load_dotenv, dotenv_values
import kfp
from kfp import dsl
from kfp import compiler
from google.cloud import aiplatform as vertex_ai
# Import pre-built Google Cloud Pipeline Components (GCPC)
from google_cloud_pipeline_components.v1 import bigquery as gcpc_bq
from google_cloud_pipeline_components.v1 import dataset as gcpc_dataset
from google_cloud_pipeline_components.v1 import endpoint as gcpc_endpoint
from google_cloud_pipeline_components.v1 import model as gcpc_model
from google_cloud_pipeline_components.v1 import automl as gcpc_automl

# Import your custom components
# Ensure src/ is in PYTHONPATH or adjust import accordingly if running from elsewhere
from src.pipeline_2025 import data_prep_comp
# from src.pipeline_2025 import bqml_training_comp # Placeholder
# from src.pipeline_2025 import automl_training_comp # Placeholder
# from src.pipeline_2025 import model_eval_comp # Placeholder

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment and Pipeline Configuration Loading ---
def load_config():
    """Loads configuration from .env file and sets up derived variables."""
    from pathlib import Path
    import os

    # Construct an absolute path to .env relative to this script file
    script_dir = Path(__file__).parent
    env_path = script_dir / '.env'
    
    logging.info(f"Attempting to load .env file from: {env_path}")
    if not env_path.exists():
        logging.error(f".env file NOT FOUND at {env_path}")
        parsed_values = {}
    else:
        logging.info(f".env file found. Size: {env_path.stat().st_size} bytes")
        # Use dotenv_values to see what is parsed without affecting os.environ yet
        parsed_values = dotenv_values(dotenv_path=env_path, verbose=True)
        logging.info(f"[DIAGNOSTIC] Values parsed by dotenv_values(): {parsed_values}")

    # Proceed to load into os.environ for the rest of the script to use
    load_dotenv(dotenv_path=env_path, override=True, verbose=True)
    
    logging.info(f"[DIAGNOSTIC] Value of SOURCE_BQ_TABLE from os.getenv after load_dotenv: {os.getenv('SOURCE_BQ_TABLE')}")
    # Optional: You can remove the full os.environ dump if parsed_values is revealing enough
    # logging.info(f"[DIAGNOSTIC] All environment variables after load_dotenv:")
    # for key, value in os.environ.items():
    #     if "KEY" in key.upper() or "TOKEN" in key.upper() or "SECRET" in key.upper():
    #         logging.info(f"  {key}=<REDACTED>")
    #     else:
    #         logging.info(f"  {key}={value}")

    config = {}

    # GCP Configuration
    config["PROJECT_ID"] = os.getenv("PROJECT")
    config["REGION"] = os.getenv("REGION")
    config["SERVICE_ACCOUNT"] = os.getenv("SERVICE_ACCOUNT")
    config["BUCKET_NAME"] = os.getenv("BUCKET")
    config["BQ_LOCATION"] = os.getenv("BQ_LOCATION")
    # config["VERTEX_AI_LOCATION"] = os.getenv("VERTEX_AI_LOCATION", config["REGION"]) # Not needed for data-prep only

    # Pipeline Configuration
    config["PIPELINE_NAME"] = os.getenv("APPNAME", "babyweight-pipeline-2025-py") # Base name
    config["PIPELINE_ROOT"] = os.getenv("PIPELINE_ROOT", f"gs://{config['BUCKET_NAME']}/pipeline_root/{config['PIPELINE_NAME']}")
    config["ENABLE_CACHING"] = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    config["TIMESTAMP"] = datetime.now().strftime("%Y%m%d%H%M%S")

    # Data Configuration
    config["SOURCE_BQ_TABLE"] = os.getenv("SOURCE_BQ_TABLE")
    config["BQ_DATASET_STAGING"] = os.getenv("BQ_DATASET_STAGING")
    config["EXTRACTED_DATA_TABLE_NAME"] = os.getenv("EXTRACTED_DATA_TABLE_NAME")
    config["PREPPED_DATA_TABLE_NAME"] = os.getenv("PREPPED_DATA_TABLE_NAME")
    config["DATA_EXTRACTION_YEAR"] = int(os.getenv("DATA_EXTRACTION_YEAR", "2000"))
    config["DATA_PREPROCESSING_LIMIT"] = int(os.getenv("DATA_PREPROCESSING_LIMIT", "100000"))

    # Use fixed table names by removing the timestamp
    config["EXTRACTED_BQ_TABLE_FULL_ID"] = f"{config['PROJECT_ID']}.{config['BQ_DATASET_STAGING']}.{config['EXTRACTED_DATA_TABLE_NAME']}"
    config["PREPPED_BQ_TABLE_FULL_ID"] = f"{config['PROJECT_ID']}.{config['BQ_DATASET_STAGING']}.{config['PREPPED_DATA_TABLE_NAME']}"

    # Removed Vertex AI Dataset, BQML, AutoML, Model Selection & Deployment configurations
    # as they are not used in the data-prep-only pipeline.

    # Validate essential configs for data prep
    for key in ["PROJECT_ID", "REGION", "BUCKET_NAME", "SOURCE_BQ_TABLE", 
                "BQ_DATASET_STAGING", "BQ_LOCATION", 
                "EXTRACTED_DATA_TABLE_NAME", "PREPPED_DATA_TABLE_NAME"]:
        if not config.get(key):
            raise ValueError(f"Missing essential configuration in .env for data prep: {key}")
    return config

# --- KFP v2 Pipeline Definition ---
def create_pipeline_definition(config: dict):
    """Defines the KFP v2 pipeline structure focusing only on data prep components."""
    @dsl.pipeline(
        name=config["PIPELINE_NAME"] + "-data-prep-only", # Indicate it's a partial pipeline
        description="Modernized baby weight data preparation pipeline (Python script version).",
        pipeline_root=config["PIPELINE_ROOT"]
    )
    def modernized_data_prep_pipeline_py(
        project_id: str = config["PROJECT_ID"],
        # region: str = config["REGION"], # Not directly used by these components if bq_location is specific
        bq_location: str = config["BQ_LOCATION"],
        # vertex_ai_resource_location: str = config["VERTEX_AI_LOCATION"], # Not used in this version
        source_bq_table: str = config["SOURCE_BQ_TABLE"],
        extracted_bq_table_full_id: str = config["EXTRACTED_BQ_TABLE_FULL_ID"],
        prepped_bq_table_full_id: str = config["PREPPED_BQ_TABLE_FULL_ID"],
        data_extraction_year: int = config["DATA_EXTRACTION_YEAR"],
        data_preprocessing_limit: int = config["DATA_PREPROCESSING_LIMIT"],
        # Removed parameters not used by data_prep_comp directly or downstream steps in this version
        # vertex_dataset_display_name: str = config["VERTEX_DATASET_DISPLAY_NAME"],
        # automl_model_display_name: str = config["AUTOML_MODEL_DISPLAY_NAME"],
        # automl_budget_milli_node_hours: int = config["AUTOML_BUDGET_MILLI_NODE_HOURS"],
        # automl_target_column: str = config["AUTOML_TARGET_COLUMN"],
        # automl_column_specs: dict = config["AUTOML_COLUMN_SPECS"],
        # bqml_model_name: str = config["BQML_MODEL_NAME"],
        # bqml_model_query: str = config["BQML_MODEL_QUERY"],
    ):
        extract_task = data_prep_comp.extract_source_data(
            project_id=project_id,
            source_bq_table_id=source_bq_table,
            extracted_bq_table_id=extracted_bq_table_full_id,
            filter_year=data_extraction_year,
            region="US"  # Explicitly set to "US" to match where the data table is located
        ).set_display_name("Extract Source Data")

        preprocess_task = data_prep_comp.preprocess_data_and_split(
            project_id=project_id,
            input_bq_table_id=extract_task.outputs["extracted_table_id"],
            preprocessed_bq_table_id=prepped_bq_table_full_id,
            data_limit=data_preprocessing_limit,
            region=bq_location # Using bq_location for the preprocess task since it works with the new table
        ).set_display_name("Preprocess and Split Data")

        logging.info("Pipeline definition created with only data prep components.")
        # Removed TabularDatasetCreateOp and all subsequent placeholder steps

    return modernized_data_prep_pipeline_py

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Compile and run the KFP ML pipeline.")
    parser.add_argument("--compile-only", action="store_true", help="Compile the pipeline and exit.")
    parser.add_argument("--run-pipeline", action="store_true", help="Compile and run the pipeline on Vertex AI.")
    args = parser.parse_args()

    logging.info("Loading pipeline configuration...")
    config = load_config()

    logging.info(f"Project ID: {config['PROJECT_ID']}")
    logging.info(f"Region: {config['REGION']}")
    logging.info(f"Pipeline Name: {config['PIPELINE_NAME']}")
    logging.info(f"Pipeline Root: {config['PIPELINE_ROOT']}")

    logging.info("Initializing Vertex AI SDK...")
    vertex_ai.init(
        project=config["PROJECT_ID"],
        location=config["REGION"],
        staging_bucket=config["PIPELINE_ROOT"]
    )

    pipeline_func = create_pipeline_definition(config)

    # Define and create the directory for compiled pipeline specifications
    COMPILED_JSON_OUTPUT_DIR = "compiled_pipeline_specs"
    os.makedirs(COMPILED_JSON_OUTPUT_DIR, exist_ok=True)
    logging.info(f"Compiled pipeline JSON specifications will be saved in: {os.path.abspath(COMPILED_JSON_OUTPUT_DIR)}")

    pipeline_json_spec_path = os.path.join(
        COMPILED_JSON_OUTPUT_DIR, 
        f"{config['PIPELINE_NAME']}_{config['TIMESTAMP']}.json"
    )

    logging.info(f"Compiling pipeline to {pipeline_json_spec_path}...")
    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=pipeline_json_spec_path,
    )
    logging.info("Pipeline compiled successfully.")

    if args.compile_only:
        logging.info("Compile-only mode. Exiting after compilation.")
        return

    if args.run_pipeline:
        logging.info("Submitting pipeline job to Vertex AI...")
        pipeline_job = vertex_ai.PipelineJob(
            display_name=f"{config['PIPELINE_NAME']}-run-{config['TIMESTAMP']}",
            template_path=pipeline_json_spec_path,
            # pipeline_root=config["PIPELINE_ROOT"], # Usually inherited from compiled spec
            enable_caching=config["ENABLE_CACHING"],
            project=config["PROJECT_ID"],
            location=config["REGION"]
        )
        try:
            # For unattended runs, use submit(). For interactive or script-based runs where you want to wait:
            # pipeline_job.submit() # Does not wait
            pipeline_job.run(service_account=config.get("SERVICE_ACCOUNT")) # Waits for completion
            logging.info(f"Pipeline job {pipeline_job.display_name} submitted and finished with state: {pipeline_job.state}.")
            logging.info(f"View in Vertex AI Pipelines: {pipeline_job._dashboard_uri()}")

            # Basic cleanup (optional, extend as needed)
            # if pipeline_job.state == vertex_ai.JobState.PIPELINE_STATE_SUCCEEDED:
            #     logging.info("Pipeline run succeeded. Performing cleanup...")
            #     # Add cleanup logic for BQ tables, models, endpoints if desired
            # else:
            #     logging.warning(f"Pipeline run did not succeed (state: {pipeline_job.state}). Skipping cleanup.")

        except Exception as e:
            logging.error(f"Error during pipeline job submission or execution: {e}")
    else:
        logging.info("To run the pipeline, use the --run-pipeline flag.")

if __name__ == "__main__":
    main() 