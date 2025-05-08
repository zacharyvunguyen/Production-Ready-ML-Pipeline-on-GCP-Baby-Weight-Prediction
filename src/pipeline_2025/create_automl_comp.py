from kfp.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple
import math

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform>=1.10.0"],
)
def collect_eval_metrics_automl(
    project_id: str,
    region: str, 
    model_artifact: Input[Artifact],
    metrics_output: Output[Metrics]
) -> NamedTuple(
    'outputs',[
        ("mean_absolute_error", float),
        ("mean_squared_error", float),
        ("root_mean_squared_error", float),
        ("r2_score", float),
        ("median_absolute_error", float),
        ("framework", str)
    ]
):   
    # Import libraries
    import google.cloud.aiplatform as aiplatform
    from google.api_core import exceptions as api_exceptions
    from collections import namedtuple
    import json
    import logging
    import math
    import time

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Define output metrics structure
    output_metric_keys = ["mean_absolute_error", "mean_squared_error", "root_mean_squared_error", "r2_score", "median_absolute_error"]
    fetched_metrics = {key: 0.0 for key in output_metric_keys}  # Initialize with 0.0 instead of NaN
    framework = "AutoML"
    OutputsType = namedtuple('outputs', output_metric_keys + ["framework"])

    # Get model resource name
    model_resource_name = model_artifact.metadata.get("resourceName")
    if not model_resource_name:
        logging.error(f"Could not get model resourceName from model artifact metadata: {model_artifact.metadata}")
        return OutputsType(**fetched_metrics, framework=framework)
    
    logging.info(f"Model resource name: {model_resource_name}")
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=region)
    
    try:
        # Initialize the start time for timeout tracking
        start_time = time.time()
        timeout_seconds = 180  # 3 minutes timeout
        
        logging.info(f"Attempting to load model: {model_resource_name}")
        # Load the model using high-level SDK
        model = aiplatform.Model(model_name=model_resource_name)
        
        # Get model evaluations with timeout check
        logging.info("Fetching model evaluations...")
        evaluations = []
        try:
            # List evaluations with timeout
            evaluation_iter = model.list_model_evaluations()
            for eval_item in evaluation_iter:
                evaluations.append(eval_item)
                # Check if we've exceeded timeout
                if time.time() - start_time > timeout_seconds:
                    logging.warning(f"Timeout after {timeout_seconds} seconds while listing evaluations")
                    break
                
            logging.info(f"Found {len(evaluations)} model evaluations")
        except Exception as eval_err:
            logging.error(f"Error listing evaluations: {eval_err}")
            # Continue with empty evaluations list
        
        # Process evaluations if we have any
        if evaluations:
            logging.info("Processing first evaluation...")
            evaluation = evaluations[0]
            metrics_dict = evaluation.metrics
            
            # Define mappings from AutoML metric names to our output names
            metric_mappings = {
                "meanAbsoluteError": "mean_absolute_error",
                "rootMeanSquaredError": "root_mean_squared_error",
                "rSquared": "r2_score",
                "medianAbsoluteError": "median_absolute_error"  # Add mapping for median if it exists
            }
            
            # Extract metrics using safe getter function
            def safe_get_metric(metrics_dict, key, default=0.0):  # Default to 0.0 instead of NaN
                try:
                    value = metrics_dict.get(key)
                    if value is None:
                        return default
                    if hasattr(value, 'number_value'):
                        return float(value.number_value)
                    return float(value)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Could not convert metric {key}: {e}")
                    return default
            
            # Extract available metrics
            for automl_key, output_key in metric_mappings.items():
                value = safe_get_metric(metrics_dict, automl_key)
                fetched_metrics[output_key] = value
                logging.info(f"Extracted {output_key} = {value}")
            
            # Calculate MSE from RMSE if available
            rmse = fetched_metrics.get("root_mean_squared_error")
            if rmse > 0:
                mse = rmse ** 2
                fetched_metrics["mean_squared_error"] = mse
                logging.info(f"Calculated MSE = {mse} from RMSE = {rmse}")
            
            # Explicitly ensure median_absolute_error is set
            if "median_absolute_error" not in fetched_metrics or fetched_metrics["median_absolute_error"] == 0.0:
                logging.info("Setting median_absolute_error to 0.0 as it was not found in AutoML metrics")
                fetched_metrics["median_absolute_error"] = 0.0
            
            # Log all metrics to KFP UI
            logging.info("Logging metrics to KFP UI...")
            for key, value in fetched_metrics.items():
                metrics_output.log_metric(key, value)
            metrics_output.log_metric("framework", framework)
            logging.info("Successfully logged all metrics")
        else:
            logging.warning("No evaluations found for model")
            # Ensure we still set all metrics with explicit default values
            logging.info("Setting all metrics to default values")
            for key in output_metric_keys:
                metrics_output.log_metric(key, 0.0)
            metrics_output.log_metric("framework", framework)
    
    except Exception as e:
        logging.error(f"Error processing model metrics: {e}")
        # Continue to return default metrics
    
    # Return the metrics, even if they're all 0.0 due to errors
    logging.info(f"Returning metrics: {fetched_metrics}")
    return OutputsType(**fetched_metrics, framework=framework)


