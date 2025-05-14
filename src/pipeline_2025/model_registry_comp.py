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
    import time
    import traceback
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    logging.info(f"Registering model: {model_name} version: {model_version}")
    logging.info(f"Project ID: {project_id}, Location: {location}")
    
    registered_model_id = "registration_failed"
    model_version_id = "registration_failed"
    
    try:
        # Extract model resource name from the artifact
        if hasattr(model, 'metadata') and 'resourceName' in model.metadata:
            model_resource_name = model.metadata['resourceName']
            logging.info(f"Model resource name from metadata: {model_resource_name}")
        else:
            model_resource_name = model.uri
            logging.info(f"Model resource name from URI: {model_resource_name}")
        
        # Dump the entire model metadata for debugging
        if hasattr(model, 'metadata'):
            logging.info(f"Full model metadata: {json.dumps(model.metadata, default=str)}")
        
        # Extract metrics
        model_metrics = {}
        try:
            if hasattr(metrics, 'metadata'):
                logging.info(f"Raw metrics metadata: {json.dumps(metrics.metadata, default=str)}")
                for key, value in metrics.metadata.items():
                    try:
                        # Try to convert to float if possible
                        model_metrics[key] = float(value)
                    except (ValueError, TypeError):
                        # Keep as string if not convertible
                        model_metrics[key] = value
        except Exception as e:
            logging.warning(f"Error extracting metrics: {e}")
            logging.warning(traceback.format_exc())
        
        logging.info(f"Processed model metrics: {model_metrics}")
        
        # Combine all metadata
        metadata = {
            "metrics": model_metrics,
            "framework": framework,
            "version": model_version,
            **additional_metadata
        }
        
        # First, verify if the model_resource_name points to a valid model
        try:
            model_exists = False
            try:
                # Try to get the model directly
                test_model = aiplatform.Model(model_name=model_resource_name)
                logging.info(f"Model exists at resource path: {model_resource_name}")
                model_exists = True
            except Exception as model_check_error:
                logging.warning(f"Could not directly access model: {model_check_error}")
            
            # Alternative approach: search for models
            logging.info(f"Searching for existing models with name: {model_name}")
            existing_models = aiplatform.Model.list(
                filter=f'display_name="{model_name}"'
            )
            
            if existing_models:
                # Update existing model with new version
                logging.info(f"Found {len(existing_models)} existing model(s) with name: {model_name}")
                model_obj = existing_models[0]
                logging.info(f"Using existing model: {model_obj.resource_name}")
                
                # Create a version alias that matches the model_version
                try:
                    # Check if the model is already uploaded to Vertex AI
                    if model_exists:
                        # If the model exists, we can use it directly
                        registered_model_id = model_obj.resource_name
                        model_version_id = model_version
                        logging.info(f"Model already exists in Vertex AI, using as is: {registered_model_id}")
                    else:
                        # Register this as a new version
                        logging.info(f"Creating new version of existing model: {model_name}")
                        logging.info(f"Model resource name: {model_resource_name}")
                        logging.info(f"Version name: {model_version}")
                        
                        # Attempt version creation with retry logic
                        max_retries = 3
                        retry_count = 0
                        while retry_count < max_retries:
                            try:
                                model_version_obj = model_obj.version(model_version)
                                # Add additional metadata to the model version
                                model_version_obj.metadata = metadata
                                model_version_obj.update()
                                registered_model_id = model_obj.resource_name
                                model_version_id = model_version
                                logging.info(f"Created version successfully: {model_version}")
                                break
                            except Exception as version_error:
                                retry_count += 1
                                if retry_count >= max_retries:
                                    raise version_error
                                logging.warning(f"Retrying version creation ({retry_count}/{max_retries}) after error: {version_error}")
                                time.sleep(2)
                except Exception as version_error:
                    logging.error(f"Error creating model version: {version_error}")
                    logging.error(traceback.format_exc())
                    raise version_error
            else:
                # Create new model entry with metadata
                logging.info(f"No existing model found. Creating new model entry: {model_name}")
                
                # If model doesn't exist in registry but exists in Vertex AI, use it directly
                if model_exists:
                    model_obj = aiplatform.Model(model_name=model_resource_name)
                    # Update display name to match our desired name
                    model_obj.update(
                        display_name=model_name,
                        description=description
                    )
                else:
                    # Upload a new model - this approach is used as a fallback
                    logging.info(f"Uploading new model: {model_name}")
                    model_obj = aiplatform.Model.upload(
                        display_name=model_name,
                        artifact_uri=model.uri,
                        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-8:latest",
                        description=description,
                        is_default_version=True
                    )
                
                # Add custom metadata
                try:
                    model_obj.metadata = metadata
                    model_obj.update()
                except Exception as metadata_error:
                    logging.warning(f"Failed to update metadata: {metadata_error}")
                
                registered_model_id = model_obj.resource_name
                model_version_id = "1"  # First version
                logging.info(f"Created new model: {registered_model_id}, Version: {model_version_id}")
            
            logging.info(f"Successfully registered model. ID: {registered_model_id}, Version: {model_version_id}")
        except Exception as model_error:
            logging.error(f"Error handling model registration: {model_error}")
            logging.error(traceback.format_exc())
            raise model_error
    except Exception as e:
        logging.error(f"Error registering model: {e}")
        logging.error(traceback.format_exc())
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