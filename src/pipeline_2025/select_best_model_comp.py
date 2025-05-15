import sys
import os
from kfp.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple

@component(
    base_image="python:3.10",
)
def select_best_model(
    automl_metrics: Input[Metrics],
    automl_model: Input[Artifact],
    bqml_metrics: Input[Metrics],
    bqml_model: Input[Artifact],
    reference_metric_name: str,
    thresholds_dict: dict
) -> NamedTuple(
    "Outputs",[
        ("deploy_decision", str),
        ("best_model_name", str),
        ("best_metric_value", float),
    ],
):
    """Selects the best model between BQML and AutoML based on specified metric.
    
    Args:
        automl_metrics: Metrics from AutoML model evaluation
        automl_model: AutoML model artifact
        bqml_metrics: Metrics from BQML model evaluation
        bqml_model: BQML model artifact
        reference_metric_name: Metric name to use for comparison (e.g., "mean_absolute_error")
        thresholds_dict: Dictionary of thresholds for deployment decision
        
    Returns:
        NamedTuple with deploy_decision, best_model_name, and best_metric_value
    """
    import logging
    from collections import namedtuple
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Standardized metric names used in both BQML and AutoML components
    standard_metric_names = [
        "mean_absolute_error",
        "mean_squared_error",
        "root_mean_squared_error",
        "r2_score",
        "median_absolute_error"
    ]
    
    # Validate reference metric name
    if reference_metric_name not in standard_metric_names:
        logging.warning(f"Reference metric {reference_metric_name} not in standard metrics: {standard_metric_names}")
        logging.info(f"Defaulting to 'mean_absolute_error' as reference metric")
        reference_metric_name = "mean_absolute_error"
    
    # For metrics where lower is better
    lower_is_better = ["mean_absolute_error", "mean_squared_error", "root_mean_squared_error", "median_absolute_error"]
    # For metrics where higher is better
    higher_is_better = ["r2_score"]
    
    logging.info(f"Comparing models using metric: {reference_metric_name}")
    logging.info(f"AutoML metrics metadata: {automl_metrics.metadata}")
    logging.info(f"BQML metrics metadata: {bqml_metrics.metadata}")
    
    # Function to safely extract metric value
    def get_metric_value(metrics_artifact, metric_name, default=None):
        try:
            # Try to get from metadata directly
            if metric_name in metrics_artifact.metadata:
                value = float(metrics_artifact.metadata[metric_name])
                logging.info(f"Found {metric_name} = {value} in metadata")
                return value
                
            # Try to get through KFP metrics method if available
            metrics_dict = getattr(metrics_artifact, "metrics", {})
            if metrics_dict and metric_name in metrics_dict:
                value = float(metrics_dict[metric_name])
                logging.info(f"Found {metric_name} = {value} in metrics dict")
                return value
                
            logging.warning(f"Metric {metric_name} not found in artifact")
            return default
        except (TypeError, ValueError) as e:
            logging.error(f"Error extracting {metric_name}: {e}")
            return default
    
    # Extract metrics from both models
    bqml_metric_value = get_metric_value(bqml_metrics, reference_metric_name, float('inf'))
    automl_metric_value = get_metric_value(automl_metrics, reference_metric_name, float('inf'))
    
    logging.info(f"BQML {reference_metric_name}: {bqml_metric_value}")
    logging.info(f"AutoML {reference_metric_name}: {automl_metric_value}")
    
    # Determine which model is better based on the metric
    if reference_metric_name in lower_is_better:
        is_bqml_better = bqml_metric_value <= automl_metric_value
    else:  # higher_is_better
        is_bqml_better = bqml_metric_value >= automl_metric_value
    
    # Select the best model
    if is_bqml_better:
        best_model_name = "BQML"
        best_metric_value = bqml_metric_value
        logging.info(f"BQML model is better with {reference_metric_name} = {best_metric_value}")
    else:
        best_model_name = "AutoML"
        best_metric_value = automl_metric_value
        logging.info(f"AutoML model is better with {reference_metric_name} = {best_metric_value}")
    
    # Determine deployment decision based on threshold
    threshold = thresholds_dict.get(reference_metric_name, float('inf'))
    
    if reference_metric_name in lower_is_better:
        deploy_decision = "true" if best_metric_value < threshold else "false"
    else:  # higher_is_better
        deploy_decision = "true" if best_metric_value > threshold else "false"
    
    # Log the decision
    logging.info(f"Best model: {best_model_name}")
    logging.info(f"Best {reference_metric_name}: {best_metric_value}")
    logging.info(f"Threshold for {reference_metric_name}: {threshold}")
    logging.info(f"Deploy decision: {deploy_decision}")
    
    # Return named tuple with results
    outputs = namedtuple("Outputs", ["deploy_decision", "best_model_name", "best_metric_value"])
    return outputs(deploy_decision, best_model_name, best_metric_value)

