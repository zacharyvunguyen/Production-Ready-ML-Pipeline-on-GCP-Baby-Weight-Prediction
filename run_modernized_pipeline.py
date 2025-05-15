import os
import json
import logging
from datetime import datetime
import argparse # For command-line arguments
import time

from dotenv import load_dotenv, dotenv_values
import kfp
from kfp import dsl
from kfp.dsl import Artifact, Metrics, importer_node
from kfp import compiler
from google.cloud import aiplatform as vertex_ai
# Import pre-built Google Cloud Pipeline Components (GCPC)
from google_cloud_pipeline_components.v1 import bigquery as gcpc_bq
# Import BigqueryCreateModelJobOp and BigqueryEvaluateModelJobOp specifically
from google_cloud_pipeline_components.v1.bigquery import BigqueryCreateModelJobOp, BigqueryEvaluateModelJobOp
from google_cloud_pipeline_components.v1 import dataset as gcpc_dataset
from google_cloud_pipeline_components.v1 import endpoint as gcpc_endpoint
from google_cloud_pipeline_components.v1 import model as gcpc_model
# from google_cloud_pipeline_components.v1 import automl as gcpc_automl # Removed incorrect import
# Correct import for AutoML training job components
from google_cloud_pipeline_components.v1.automl.training_job import AutoMLTabularTrainingJobRunOp
# Import ModelDeployOp from endpoint module
from google_cloud_pipeline_components.v1.endpoint import ModelDeployOp
# from google_cloud_pipeline_components.v1.model.export_model import ModelExportOp
# from google_cloud_pipeline_components.v1.model.upload_model import ModelUploadOp
from google_cloud_pipeline_components.v1.dataset import TabularDatasetCreateOp
from google_cloud_pipeline_components.types import artifact_types
# Remove import for notification email component

# Import your custom components
# Ensure src/ is in PYTHONPATH or adjust import accordingly if running from elsewhere
from src.pipeline_2025 import data_prep_comp
# from src.pipeline_2025 import bqml_training_comp # Placeholder
# from src.pipeline_2025 import automl_training_comp # Placeholder
# from src.pipeline_2025 import model_eval_comp # Placeholder
# Import the BQML component module
from src.pipeline_2025 import create_bqml_comp
# Import the AutoML component module
from src.pipeline_2025 import create_automl_comp
# Import the Model Selection component
from src.pipeline_2025 import select_best_model_comp
# Import helper component
from src.pipeline_2025 import helper_components
# Import the new endpoint management and model registry components
from src.pipeline_2025 import endpoint_management_comp
from src.pipeline_2025 import model_registry_comp

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

    # BQML Configuration (add these)
    config["BQML_MODEL_NAME"] = os.getenv("BQML_MODEL_NAME", "bqml_babyweight_dnn_combined")
    config["BQML_MODEL_VERSION_ALIASES"] = os.getenv("BQML_MODEL_VERSION_ALIASES", "v1") # Example default
    config["VAR_TARGET"] = os.getenv("VAR_TARGET", "weight_pounds") # Your target variable

    # Prepare formatted BQML version aliases
    raw_aliases = config["BQML_MODEL_VERSION_ALIASES"]
    aliases_list = [alias.strip() for alias in raw_aliases.split(',')]
    config["FORMATTED_BQML_MODEL_VERSION_ALIASES"] = '[' + ', '.join([f"'{alias}'" for alias in aliases_list]) + ']'

    # AutoML Configuration - Add these
    # Ensure PIPELINE_NAME is available before being used in f-string defaults
    pipeline_name_for_defaults = config.get("PIPELINE_NAME", "baby-mlops-pipeline") # Fallback if PIPELINE_NAME somehow not set yet
    config["VERTEX_DATASET_DISPLAY_NAME"] = os.getenv("VERTEX_DATASET_DISPLAY_NAME", f"{pipeline_name_for_defaults}-vertex-dataset")
    config["AUTOML_MODEL_DISPLAY_NAME"] = os.getenv("AUTOML_MODEL_DISPLAY_NAME", f"{pipeline_name_for_defaults}-automl-model")
    config["AUTOML_BUDGET_MILLI_NODE_HOURS"] = int(os.getenv("AUTOML_BUDGET_MILLI_NODE_HOURS", "1000"))
    # Create the combined display name for the training job itself
    config["AUTOML_TRAINING_JOB_DISPLAY_NAME"] = f'{config["AUTOML_MODEL_DISPLAY_NAME"]}_TrainingJob'

    # Model Selection Configuration
    config["COMPARISON_METRIC"] = os.getenv("COMPARISON_METRIC", "mean_absolute_error")
    # Default thresholds for deployment decision
    default_thresholds = {
        "mean_absolute_error": 0.9,
        "mean_squared_error": 1.2,
        "root_mean_squared_error": 1.1,
        "r2_score": 0.35  # For r2_score, higher is better, so this is a minimum threshold
    }
    # Try to parse JSON from environment variable, fallback to defaults if not provided
    thresholds_str = os.getenv("MODEL_THRESHOLDS_JSON", "")
    if thresholds_str:
        try:
            config["MODEL_THRESHOLDS"] = json.loads(thresholds_str)
        except json.JSONDecodeError:
            logging.warning(f"Could not parse MODEL_THRESHOLDS_JSON: {thresholds_str}. Using defaults.")
            config["MODEL_THRESHOLDS"] = default_thresholds
    else:
        config["MODEL_THRESHOLDS"] = default_thresholds
        
    logging.info(f"Model comparison metric: {config['COMPARISON_METRIC']}")
    logging.info(f"Model thresholds: {config['MODEL_THRESHOLDS']}")

    # Deployment Configuration
    config["ENDPOINT_DISPLAY_NAME"] = os.getenv("ENDPOINT_DISPLAY_NAME", f"{pipeline_name_for_defaults}-endpoint")
    config["DEPLOY_MACHINE_TYPE"] = os.getenv("DEPLOY_MACHINE_TYPE", "n1-standard-2")
    config["DEPLOY_MIN_REPLICA_COUNT"] = int(os.getenv("DEPLOY_MIN_REPLICA_COUNT", "1"))
    config["DEPLOY_MAX_REPLICA_COUNT"] = int(os.getenv("DEPLOY_MAX_REPLICA_COUNT", "1"))
    
    # For column_specs, it's better to define it in Python or load from a dedicated JSON file if complex.
    # For simplicity here, we'll assume a simple default or expect it to be well-formed if set via .env.
    automl_column_specs_json = os.getenv("AUTOML_COLUMN_SPECS_JSON")
    if automl_column_specs_json:
        try:
            config["AUTOML_COLUMN_SPECS"] = json.loads(automl_column_specs_json)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding AUTOML_COLUMN_SPECS_JSON: {e}. Using empty dict as fallback.")
            config["AUTOML_COLUMN_SPECS"] = {}
    else:
        # Define a default if not provided, or make it mandatory in validation
        # Generate default 'auto' specs for known features if not provided
        logging.info("AUTOML_COLUMN_SPECS_JSON not found in .env. Generating default 'auto' specs.")
        feature_columns = [
            "is_male", 
            "mother_age", 
            "plurality_category", 
            "gestation_weeks", 
            "cigarette_use_str", 
            "alcohol_use_str"
        ]
        config["AUTOML_COLUMN_SPECS"] = {col: "auto" for col in feature_columns}
        logging.info(f"Generated default AUTOML_COLUMN_SPECS: {config['AUTOML_COLUMN_SPECS']}")

    # Use fixed table names by removing the timestamp
    config["EXTRACTED_BQ_TABLE_FULL_ID"] = f"{config['PROJECT_ID']}.{config['BQ_DATASET_STAGING']}.{config['EXTRACTED_DATA_TABLE_NAME']}"
    config["PREPPED_BQ_TABLE_FULL_ID"] = f"{config['PROJECT_ID']}.{config['BQ_DATASET_STAGING']}.{config['PREPPED_DATA_TABLE_NAME']}"

    # Removed Vertex AI Dataset, BQML, AutoML, Model Selection & Deployment configurations
    # as they are not used in the data-prep-only pipeline.

    # Validate essential configs for data prep
    for key in ["PROJECT_ID", "REGION", "BUCKET_NAME", "SOURCE_BQ_TABLE", 
                "BQ_DATASET_STAGING", "BQ_LOCATION", 
                "EXTRACTED_DATA_TABLE_NAME", "PREPPED_DATA_TABLE_NAME",
                "BQML_MODEL_NAME", "VAR_TARGET",
                "VERTEX_DATASET_DISPLAY_NAME", "AUTOML_MODEL_DISPLAY_NAME", "AUTOML_BUDGET_MILLI_NODE_HOURS"]:
        if not config.get(key):
            raise ValueError(f"Missing essential configuration in .env for data prep: {key}")
    return config

# --- KFP v2 Pipeline Definition ---
def create_pipeline_definition(config: dict):
    """Defines the KFP v2 pipeline structure including data prep, BQML and AutoML training, and evaluation."""
    @dsl.pipeline(
        name=config["PIPELINE_NAME"] + "-bqml-automl-train-eval",
        description="Modernized baby weight pipeline with data prep, BQML & AutoML training, and evaluation.",
        pipeline_root=config["PIPELINE_ROOT"]
    )
    def modernized_full_pipeline_py(
        project_id: str = config["PROJECT_ID"],
        bq_location: str = config["BQ_LOCATION"],
        source_bq_table: str = config["SOURCE_BQ_TABLE"],
        extracted_bq_table_full_id: str = config["EXTRACTED_BQ_TABLE_FULL_ID"],
        prepped_bq_table_full_id: str = config["PREPPED_BQ_TABLE_FULL_ID"],
        data_extraction_year: int = config["DATA_EXTRACTION_YEAR"],
        data_preprocessing_limit: int = config["DATA_PREPROCESSING_LIMIT"],
        bqml_model_name: str = config["BQML_MODEL_NAME"],
        formatted_bqml_model_version_aliases: str = config["FORMATTED_BQML_MODEL_VERSION_ALIASES"],
        var_target: str = config["VAR_TARGET"],
        # AutoML Parameters - Added
        vertex_dataset_display_name: str = config["VERTEX_DATASET_DISPLAY_NAME"],
        # Use the combined training job display name
        automl_training_job_display_name: str = config["AUTOML_TRAINING_JOB_DISPLAY_NAME"], 
        # Keep the base model display name for the model itself
        automl_model_display_name_param: str = config["AUTOML_MODEL_DISPLAY_NAME"], 
        automl_budget_milli_node_hours: int = config["AUTOML_BUDGET_MILLI_NODE_HOURS"],
        automl_column_specs: dict = config["AUTOML_COLUMN_SPECS"],
        region: str = config["REGION"], # Added region for AutoML components that might need it
        # Model Selection Parameters
        comparison_metric: str = config["COMPARISON_METRIC"],
        model_thresholds: dict = config["MODEL_THRESHOLDS"],
        # Deployment Parameters
        endpoint_display_name: str = config["ENDPOINT_DISPLAY_NAME"],
        deploy_machine_type: str = config["DEPLOY_MACHINE_TYPE"],
        deploy_min_replica_count: int = config["DEPLOY_MIN_REPLICA_COUNT"],
        deploy_max_replica_count: int = config["DEPLOY_MAX_REPLICA_COUNT"],
    ):
        # Data extraction component - use the existing extract_source_data component
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

        # --- BQML Branch ---
        # --- Add BQML Training Step --- 
        # Create a deterministic model ID for caching purposes, or unique ID for production
        if config["ENABLE_CACHING"]:
            # When caching is enabled, use a stable identifier to allow task caching
            vertex_model_id = f"{bqml_model_name}-cached"
        else:
            # When caching is disabled or in production, use a unique identifier
            vertex_model_id = f"{bqml_model_name}-{config['TIMESTAMP']}"
        
        train_query = create_bqml_comp.create_query_build_bqml_model(
            project=project_id,
            bq_dataset=config["BQ_DATASET_STAGING"],
            bq_model_name=bqml_model_name,
            formatted_bq_version_aliases=formatted_bqml_model_version_aliases,
            var_target=var_target,
            bq_train_table_id=preprocess_task.outputs["preprocessed_table_id"],
            model_registry="vertex_ai",  # Add this to register directly with Vertex AI
            vertex_ai_model_id=vertex_model_id  # Use our cache-friendly or unique ID
        )

        bqml_train_task = gcpc_bq.BigqueryCreateModelJobOp(
            project=project_id,
            location=bq_location,
            query=train_query,
        ).set_display_name("Train BQML Model").after(preprocess_task)

        # Construct the Vertex AI Model resource name string using the helper component
        construct_name_task = helper_components.construct_vertex_model_resource_name(
            project_id=project_id,
            region=region, # Ensure this is the region where the Vertex AI model is registered
            vertex_model_id=vertex_model_id # This is already defined based on caching settings
        ).set_display_name("Construct Vertex Model Name").after(bqml_train_task) # Runs after BQML training ensures model exists

        # Import the BQML model (now in Vertex AI Registry) as a VertexModel artifact for KFP
        bqml_model_importer_task = importer_node.importer(
            artifact_uri=construct_name_task.outputs["vertex_model_resource_name_str"],
            artifact_class=artifact_types.VertexModel,
            metadata={'resourceName': construct_name_task.outputs["vertex_model_resource_name_str"]} 
        ).set_display_name("Import BQML as VertexModel Artifact").after(construct_name_task)

        # --- Add BQML Evaluation Step --- 
        bqml_evaluate_task = gcpc_bq.BigqueryEvaluateModelJobOp(
            project=project_id, 
            location=bq_location, 
            model=bqml_train_task.outputs["model"] 
        ).set_display_name('Evaluate BQML Model').after(bqml_train_task)

        # --- Add BQML Metrics Collection Step --- 
        collect_bqml_metrics_task = create_bqml_comp.collect_eval_metrics_bqml(
            eval_metrics_artifact=bqml_evaluate_task.outputs["evaluation_metrics"]
        ).set_display_name('Collect BQML Metrics').after(bqml_evaluate_task)

        # --- AutoML Branch ---
        # --- Create Vertex AI Dataset for AutoML --- 
        vertex_dataset_task = gcpc_dataset.TabularDatasetCreateOp(
            project=project_id,
            display_name=vertex_dataset_display_name,
            bq_source=f'bq://{preprocess_task.outputs["preprocessed_table_id"]}',
            location=region # Use the main region for Vertex AI resources
        ).set_display_name("Create Vertex AI Dataset").after(preprocess_task)

        # --- Train AutoML Model ---
        automl_train_task = AutoMLTabularTrainingJobRunOp(
            project=project_id,
            # Use the pipeline parameter for the job display name
            display_name=automl_training_job_display_name,
            optimization_prediction_type="regression",
            optimization_objective="minimize-rmse",
            budget_milli_node_hours=automl_budget_milli_node_hours,
            # Use the pipeline parameter for the model display name itself
            model_display_name=automl_model_display_name_param, 
            dataset=vertex_dataset_task.outputs["dataset"],
            target_column=var_target, 
            column_specs=automl_column_specs,
            location=region # Use the main region for Vertex AI resources
        ).set_display_name("Train AutoML Model").after(vertex_dataset_task)

        # Collect AutoML Model evaluation metrics
        collect_automl_metrics_task = create_automl_comp.collect_eval_metrics_automl(
            project_id=project_id,
            region=region,
            model_artifact=automl_train_task.outputs["model"],
        ).set_display_name("Collect AutoML Metrics").after(automl_train_task)

        # --- Model Selection - Compare BQML and AutoML models ---
        select_model_task = select_best_model_comp.select_best_model(
            automl_metrics=collect_automl_metrics_task.outputs["metrics_output"],
            automl_model=automl_train_task.outputs["model"],
            bqml_metrics=collect_bqml_metrics_task.outputs["metrics"],
            bqml_model=bqml_train_task.outputs["model"],
            reference_metric_name=comparison_metric,
            thresholds_dict=model_thresholds
        ).set_display_name("Select Best Model").after(collect_bqml_metrics_task, collect_automl_metrics_task)
        
        # Log the outputs from the selection task for visibility
        logging.info(f"Model selection task added with outputs: {select_model_task.outputs}")
        
        # Log which model was selected and the deployment decision
        best_model_name = select_model_task.outputs["best_model_name"]
        deploy_decision = select_model_task.outputs["deploy_decision"]
        best_metric = select_model_task.outputs["best_metric_value"]
        
        # Fix: Use string literals for logging instead of pipeline parameters directly
        logging.info("Pipeline will select best model based on configured metric")
        logging.info("Deployment decision will be based on model performance threshold")

        # --- Deployment - Create Endpoint and Deploy Best Model ---
        # Create endpoint for model deployment using standard component (unmodified)
        standard_endpoint_task = gcpc_endpoint.EndpointCreateOp(
            project=project_id,
            location=region,
            display_name=endpoint_display_name
        ).set_display_name("Create Endpoint")
        
        # Add separate endpoint check task that runs in parallel and doesn't affect the original flow
        endpoint_check_task = endpoint_management_comp.get_or_create_endpoint(
            project_id=project_id,
            location=region,
            display_name=endpoint_display_name
        ).set_display_name("Check Existing Endpoint")

        # Only deploy if the model meets the threshold criteria
        with dsl.If(
            select_model_task.outputs["deploy_decision"] == "true",
            name="deployment_qualification_check"
        ):
            # For AutoML model
            with dsl.If(
                select_model_task.outputs["best_model_name"] == "AutoML",
                name="model_type_selector"
            ):
                # Register AutoML model
                register_automl_task = model_registry_comp.register_best_model_in_registry(
                    model=automl_train_task.outputs["model"],
                    model_name=f"{config['PIPELINE_NAME']}-automl-model",
                    model_version=config['TIMESTAMP'],
                    metrics=collect_automl_metrics_task.outputs["metrics_output"],
                    project_id=project_id,
                    location=region,
                    description=f"AutoML model selected by pipeline run at {config['TIMESTAMP']}",
                    additional_metadata={
                        "pipeline_run_id": dsl.PIPELINE_JOB_ID_PLACEHOLDER,
                        "model_type": "AutoML",
                        "comparison_metric": config["COMPARISON_METRIC"],
                        "metric_source": "automl_metrics"
                    }
                ).set_display_name("Register AutoML Model").after(select_model_task)
                
                # Deploy AutoML model - now using the registered model ID and version
                automl_deploy_task = ModelDeployOp(
                    model=automl_train_task.outputs["model"],
                    endpoint=standard_endpoint_task.outputs["endpoint"],
                    dedicated_resources_machine_type=deploy_machine_type,
                    dedicated_resources_min_replica_count=deploy_min_replica_count,
                    dedicated_resources_max_replica_count=deploy_max_replica_count,
                    traffic_split={"0": 100},
                    # Adding display metadata to track model info 
                    deployed_model_display_name=f"AutoML-Model-{config['TIMESTAMP']}"
                ).set_display_name("Deploy AutoML Model").after(standard_endpoint_task, register_automl_task)
                
                # Log model registration info
                log_model_info_task = helper_components.log_model_details(
                    model_id=register_automl_task.outputs["registered_model_id"],
                    model_version=register_automl_task.outputs["model_version_id"],
                    model_type="AutoML"
                ).set_display_name("Log AutoML Model Info").after(register_automl_task)
                
                # Add traffic management without modifying the original flow
                with dsl.If(endpoint_check_task.outputs["is_new_endpoint"] == False,
                           name="traffic_update_decision"):
                    update_traffic_task = endpoint_management_comp.update_traffic_split(
                        project_id=project_id,
                        location=region,
                        endpoint_resource_name=endpoint_check_task.outputs["endpoint_resource_name"],
                        deployed_model_id="PLACEHOLDER_ID", # We'll update this in the component
                        traffic_percentage=100,  # Give full traffic to new model
                        # Pass registered model information for better tracking
                        registered_model_id=register_automl_task.outputs["registered_model_id"],
                        model_version_id=register_automl_task.outputs["model_version_id"]
                    ).set_display_name("Update Traffic Split").after(automl_deploy_task)
            
            # For BQML model
            with dsl.Elif(
                select_model_task.outputs["best_model_name"] == "BQML",
                name="register_bqml"
            ):
                # Register BQML model
                register_bqml_task = model_registry_comp.register_best_model_in_registry(
                    model=bqml_model_importer_task.outputs["artifact"],
                    model_name=f"{config['PIPELINE_NAME']}-bqml-model",
                    model_version=config['TIMESTAMP'],
                    metrics=collect_bqml_metrics_task.outputs["metrics"],
                    project_id=project_id,
                    location=region,
                    description=f"BQML model selected by pipeline run at {config['TIMESTAMP']}",
                    additional_metadata={
                        "pipeline_run_id": dsl.PIPELINE_JOB_ID_PLACEHOLDER,
                        "model_type": "BQML",
                        "comparison_metric": config["COMPARISON_METRIC"],
                        "metric_source": "bqml_metrics"
                    }
                ).set_display_name("Register BQML Model").after(select_model_task)
                
                # Log model registration info
                log_model_info_task = helper_components.log_model_details(
                    model_id=register_bqml_task.outputs["registered_model_id"],
                    model_version=register_bqml_task.outputs["model_version_id"],
                    model_type="BQML"
                ).set_display_name("Log BQML Model Info").after(register_bqml_task)
                
                # Deploy BQML model - now using the registered model ID and version
                bqml_deploy_task = ModelDeployOp(
                    model=bqml_model_importer_task.outputs["artifact"], # Use the imported VertexModel artifact
                    endpoint=standard_endpoint_task.outputs["endpoint"],
                    dedicated_resources_machine_type=deploy_machine_type,
                    dedicated_resources_min_replica_count=deploy_min_replica_count,
                    dedicated_resources_max_replica_count=deploy_max_replica_count,
                    traffic_split={"0": 100},
                    # Adding display metadata to track model info
                    deployed_model_display_name=f"BQML-Model-{config['TIMESTAMP']}"
                ).set_display_name("Deploy BQML Model").after(standard_endpoint_task, register_bqml_task)
                
                # Add traffic management without modifying the original flow
                with dsl.If(endpoint_check_task.outputs["is_new_endpoint"] == False,
                           name="traffic_update_decision"):
                    update_traffic_task = endpoint_management_comp.update_traffic_split(
                        project_id=project_id,
                        location=region,
                        endpoint_resource_name=endpoint_check_task.outputs["endpoint_resource_name"],
                        deployed_model_id="PLACEHOLDER_ID", # We'll update this in the component
                        traffic_percentage=100,  # Give full traffic to new model
                        # Pass registered model information for better tracking
                        registered_model_id=register_bqml_task.outputs["registered_model_id"],
                        model_version_id=register_bqml_task.outputs["model_version_id"]
                    ).set_display_name("Update Traffic Split").after(bqml_deploy_task)

    return modernized_full_pipeline_py

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
        f"{config['PIPELINE_NAME']}-bqml-automl-train-eval_{config['TIMESTAMP']}.json"
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
            display_name=f"{config['PIPELINE_NAME']}-bqml-automl-train-eval-run-{config['TIMESTAMP']}",
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