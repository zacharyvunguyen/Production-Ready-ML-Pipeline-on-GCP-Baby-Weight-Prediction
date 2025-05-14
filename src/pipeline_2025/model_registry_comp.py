from kfp.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def register_best_model_in_registry(
    model: Input[Artifact],
    model_name: str,
    model_version: str,
    metrics: Input[Metrics],
    project_id: str,
    location: str,
    model_registry_id: str = "default",
    description: str = "",
    framework: str = "tensorflow",
    additional_metadata: dict = {},
) -> NamedTuple("Outputs", [
    ("registered_model_id", str),
    ("model_version_id", str)
]):
    """Registers a model in the Vertex AI Model Registry.
    
    Args:
        model: Input model artifact
        model_name: Name of the model
        model_version: Model version
        metrics: Metrics for the model
        project_id: GCP project ID
        location: GCP region
        model_registry_id: ID of the model registry (default: "default")
        description: Description of the model
        framework: ML framework used (tensorflow, pytorch, xgboost, sklearn)
        additional_metadata: Additional metadata to attach to the model
    
    Returns:
        registered_model_id: ID of the registered model
        model_version_id: ID of the model version
    """
    import logging
    from google.cloud import aiplatform
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    logging.info(f"Registering model: {model_name} version: {model_version}")
    
    # Extract model resource name from the artifact
    if hasattr(model, 'metadata') and 'resourceName' in model.metadata:
        model_resource_name = model.metadata['resourceName']
    else:
        model_resource_name = model.uri
    
    logging.info(f"Model resource name: {model_resource_name}")
    
    # Extract metrics
    model_metrics = {}
    try:
        if hasattr(metrics, 'metadata'):
            for key, value in metrics.metadata.items():
                try:
                    # Try to convert to float if possible
                    model_metrics[key] = float(value)
                except (ValueError, TypeError):
                    # Keep as string if not convertible
                    model_metrics[key] = value
    except Exception as e:
        logging.warning(f"Error extracting metrics: {e}")
    
    logging.info(f"Model metrics: {model_metrics}")
    
    # Combine all metadata
    metadata = {
        "metrics": model_metrics,
        "framework": framework,
        "version": model_version,
        **additional_metadata
    }
    
    # Get the model from Vertex AI
    try:
        # Try to get existing model by name first
        existing_models = aiplatform.Model.list(
            filter=f'display_name="{model_name}"'
        )
        
        if existing_models:
            # Update existing model with new version
            logging.info(f"Found existing model with name: {model_name}")
            model_obj = existing_models[0]
            
            # Register this as a new version
            model_version_obj = model_obj.create_version(
                model_resource_name=model_resource_name,
                version_name=model_version,
                description=description,
                metadata={
                    "metrics": json.dumps(model_metrics),
                    "framework": framework,
                    **additional_metadata
                }
            )
            registered_model_id = model_obj.resource_name
            model_version_id = model_version_obj.version_id
        else:
            # Create new model entry with metadata
            logging.info(f"Creating new model entry: {model_name}")
            model_obj = aiplatform.Model(model_resource_name)
            
            # Update model metadata
            model_obj.update(
                display_name=model_name,
                description=description,
                metadata_schema_uri=f"https://googleapis.com/vertexai/ml/metadata/schemas/{framework}/1"
            )
            
            # Add custom metadata
            model_obj.metadata = metadata
            model_obj.update()
            
            registered_model_id = model_obj.resource_name
            model_version_id = "1"  # First version
        
        logging.info(f"Successfully registered model. ID: {registered_model_id}, Version: {model_version_id}")
    except Exception as e:
        logging.error(f"Error registering model: {e}")
        registered_model_id = "registration_failed"
        model_version_id = "registration_failed"
    
    from collections import namedtuple
    outputs = namedtuple("Outputs", ["registered_model_id", "model_version_id"])
    return outputs(registered_model_id, model_version_id)

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def get_model_lineage(
    model_id: str,
    project_id: str,
    location: str,
) -> NamedTuple("Outputs", [
    ("lineage_data", dict),
    ("lineage_json", str)
]):
    """Retrieves the lineage information for a model from Vertex AI.
    
    Args:
        model_id: The full resource name of the model
        project_id: GCP project ID
        location: GCP region
    
    Returns:
        lineage_data: Dictionary containing lineage data
        lineage_json: JSON string representation of lineage data
    """
    import logging
    from google.cloud import aiplatform
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    logging.info(f"Retrieving lineage for model: {model_id}")
    
    try:
        # Get the model object
        model = aiplatform.Model(model_name=model_id)
        
        # Get metadata
        metadata = model.metadata
        
        # Get model versions (if applicable)
        try:
            versions = model.list_versions()
            version_info = [{
                "version_id": v.version_id,
                "create_time": v.create_time.isoformat() if hasattr(v, 'create_time') else None,
                "update_time": v.update_time.isoformat() if hasattr(v, 'update_time') else None
            } for v in versions]
        except Exception as e:
            logging.warning(f"Error getting model versions: {e}")
            version_info = []
        
        # Construct lineage data
        lineage_data = {
            "model_id": model_id,
            "display_name": model.display_name,
            "create_time": model.create_time.isoformat() if hasattr(model, 'create_time') else None,
            "update_time": model.update_time.isoformat() if hasattr(model, 'update_time') else None,
            "metadata": metadata,
            "versions": version_info
        }
        
        lineage_json = json.dumps(lineage_data, indent=2)
        logging.info(f"Successfully retrieved model lineage")
    except Exception as e:
        logging.error(f"Error retrieving model lineage: {e}")
        lineage_data = {"error": str(e)}
        lineage_json = json.dumps(lineage_data)
    
    from collections import namedtuple
    outputs = namedtuple("Outputs", ["lineage_data", "lineage_json"])
    return outputs(lineage_data, lineage_json) 