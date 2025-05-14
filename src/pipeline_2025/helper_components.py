from kfp.dsl import component
from typing import NamedTuple

@component(
    base_image="python:3.10",
    packages_to_install=[]
)
def construct_vertex_model_resource_name(
    project_id: str,
    region: str,
    vertex_model_id: str,
) -> NamedTuple("Outputs", [
    ("vertex_model_resource_name_str", str),
]):
    """Constructs the full Vertex AI model resource name string from components.
    
    Args:
        project_id: GCP project ID
        region: GCP region where model is located
        vertex_model_id: The specific ID of the model
    
    Returns:
        vertex_model_resource_name_str: The fully-qualified resource name for the model
    """
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Construct Vertex AI model resource name
    resource_name = f"projects/{project_id}/locations/{region}/models/{vertex_model_id}"
    
    logging.info(f"Constructed Vertex AI model resource name: {resource_name}")
    
    from collections import namedtuple
    outputs = namedtuple("Outputs", ["vertex_model_resource_name_str"])
    return outputs(resource_name)

@component(
    base_image="python:3.10",
    packages_to_install=[]
)
def log_model_details(
    model_id: str,
    model_version: str,
    model_type: str
) -> NamedTuple("Outputs", [
    ("model_info_json", str),
]):
    """Logs model registration and deployment details for tracking.
    
    Args:
        model_id: The full resource name of the registered model
        model_version: The version ID of the registered model
        model_type: The type of model (AutoML or BQML)
    
    Returns:
        model_info_json: JSON string containing model information
    """
    import logging
    import json
    import datetime
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Collect model details
    model_info = {
        "model_id": model_id,
        "model_version": model_version,
        "model_type": model_type,
        "registration_time": datetime.datetime.now().isoformat(),
    }
    
    # Convert to JSON
    model_info_json = json.dumps(model_info, indent=2)
    
    # Log the model info
    logging.info(f"Model Registration Information:")
    logging.info(f"  - Model ID: {model_id}")
    logging.info(f"  - Model Version: {model_version}")
    logging.info(f"  - Model Type: {model_type}")
    logging.info(f"  - Registration Time: {model_info['registration_time']}")
    
    from collections import namedtuple
    outputs = namedtuple("Outputs", ["model_info_json"])
    return outputs(model_info_json) 