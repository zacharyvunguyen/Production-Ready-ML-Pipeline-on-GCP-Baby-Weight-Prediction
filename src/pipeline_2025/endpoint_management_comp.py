from kfp.dsl import Artifact, Output, Input, component
from typing import NamedTuple

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def get_or_create_endpoint(
    project_id: str,
    location: str,
    display_name: str,
) -> NamedTuple("Outputs", [
    ("endpoint", Artifact),
    ("endpoint_resource_name", str),
    ("is_new_endpoint", bool)
]):
    """Gets or creates a Vertex AI endpoint.
    
    This component will first check if an endpoint with the given display name 
    exists. If it does, it returns that endpoint. Otherwise, it creates a new one.
    
    Args:
        project_id: The GCP project ID
        location: The GCP region where the endpoint should be created
        display_name: Display name for the endpoint
        
    Returns:
        endpoint: The Vertex AI endpoint artifact
        endpoint_resource_name: The full resource name of the endpoint
        is_new_endpoint: Whether a new endpoint was created
    """
    import logging
    from google.cloud import aiplatform
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    # Check for existing endpoints with this display name
    logging.info(f"Checking for existing endpoint with display name: {display_name}")
    endpoints = aiplatform.Endpoint.list(
        filter=f'display_name="{display_name}"',
        order_by="create_time desc"
    )
    
    is_new_endpoint = False
    
    if endpoints and len(endpoints) > 0:
        # Use existing endpoint
        endpoint = endpoints[0]
        logging.info(f"Found existing endpoint with ID: {endpoint.name}")
    else:
        # Create new endpoint
        logging.info(f"No existing endpoint found. Creating a new one with display name: {display_name}")
        endpoint = aiplatform.Endpoint.create(display_name=display_name)
        is_new_endpoint = True
        logging.info(f"Created new endpoint with ID: {endpoint.name}")
    
    # Prepare output values
    endpoint_resource_name = endpoint.resource_name
    
    from collections import namedtuple
    outputs = namedtuple("Outputs", ["endpoint", "endpoint_resource_name", "is_new_endpoint"])
    
    # Create endpoint artifact
    endpoint_artifact = Artifact()
    endpoint_artifact.uri = endpoint_resource_name
    endpoint_artifact.metadata = {"resourceName": endpoint_resource_name}
    
    return outputs(endpoint_artifact, endpoint_resource_name, is_new_endpoint)

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def update_traffic_split(
    project_id: str,
    location: str, 
    endpoint_resource_name: str,
    deployed_model_id: str,
    traffic_percentage: int = 100,
    registered_model_id: str = "",
    model_version_id: str = "",
) -> NamedTuple("Outputs", [
    ("deployed_model_id", str),
    ("model_details", dict)
]):
    """Updates traffic split for a deployed model on an endpoint.
    
    Args:
        project_id: The GCP project ID
        location: The GCP region
        endpoint_resource_name: The full resource name of the endpoint
        deployed_model_id: ID of the deployed model to direct traffic to, or "PLACEHOLDER_ID" to use the most recently deployed model
        traffic_percentage: Percentage of traffic to route to the model (0-100)
        registered_model_id: The full resource name of the registered model (from Model Registry)
        model_version_id: The version ID of the registered model
        
    Returns:
        deployed_model_id: The ID of the deployed model that received traffic
        model_details: Dictionary with details about the model and deployment
    """
    import logging
    from google.cloud import aiplatform
    from collections import namedtuple
    import time
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    # Get the endpoint
    logging.info(f"Retrieving endpoint: {endpoint_resource_name}")
    endpoint = aiplatform.Endpoint(endpoint_name=endpoint_resource_name)
    
    # Model details dictionary to return
    model_details = {
        "endpoint_id": endpoint_resource_name,
        "registered_model_id": registered_model_id,
        "model_version_id": model_version_id,
        "deployment_time": "",
        "traffic_percentage": traffic_percentage
    }
    
    actual_model_id = ""  # Will store the resolved model ID
    
    # Get current deployed models
    try:
        # Wait longer to ensure model deployment is completed - deployment can take time
        # Using a retry approach with exponential backoff
        max_retries = 5
        base_wait_time = 30  # seconds
        
        deployed_models = []
        
        for attempt in range(max_retries):
            # Calculate wait time with exponential backoff
            wait_time = base_wait_time * (2 ** attempt)
            logging.info(f"Attempt {attempt+1}/{max_retries}: Waiting {wait_time} seconds for model deployment to complete...")
            time.sleep(wait_time)
            
            # Refresh endpoint information
            endpoint = aiplatform.Endpoint(endpoint_name=endpoint_resource_name)
            
            # Check if there are deployed models
            if hasattr(endpoint.gca_resource, 'deployed_models') and endpoint.gca_resource.deployed_models:
                deployed_models = endpoint.gca_resource.deployed_models
                logging.info(f"Found {len(deployed_models)} deployed models on endpoint")
                # If we're looking for a specific ID and it's there, we can break early
                if deployed_model_id != "PLACEHOLDER_ID" and any(m.id == deployed_model_id for m in deployed_models):
                    logging.info(f"Found specified model ID: {deployed_model_id}")
                    break
                # If using PLACEHOLDER_ID, having any models is enough
                if deployed_model_id == "PLACEHOLDER_ID" and deployed_models:
                    logging.info("Using most recent deployed model")
                    break
            else:
                logging.info("No deployed models found yet, continuing to wait...")
        
        # Handle placeholder ID by finding the most recent model
        if deployed_model_id == "PLACEHOLDER_ID":
            if deployed_models:
                # Extract creation times safely - models should have create_time but handle if missing
                sorted_models = []
                for model in deployed_models:
                    # Try different attributes that might exist for creation time
                    if hasattr(model, 'create_time') and model.create_time:
                        try:
                            # Convert to seconds for comparison if possible
                            if hasattr(model.create_time, 'seconds'):
                                time_value = model.create_time.seconds
                            else:
                                # Fall back to string representation for sorting
                                time_value = str(model.create_time)
                            sorted_models.append((model, time_value))
                        except Exception as e:
                            logging.warning(f"Error processing create_time for model {model.id}: {e}")
                            # Add with a default sort value
                            sorted_models.append((model, 0))
                    else:
                        # No create_time attribute, add with default value
                        sorted_models.append((model, 0))
                
                # Sort by time value (descending)
                sorted_models.sort(key=lambda x: x[1], reverse=True)
                
                if sorted_models:
                    actual_model_id = sorted_models[0][0].id
                    logging.info(f"Using most recently deployed model with ID: {actual_model_id}")
                    
                    # Add deployment time to model details if available
                    model = sorted_models[0][0]
                    if hasattr(model, 'create_time'):
                        try:
                            if hasattr(model.create_time, 'ToDatetime'):
                                model_details["deployment_time"] = model.create_time.ToDatetime().isoformat()
                            else:
                                model_details["deployment_time"] = str(model.create_time)
                        except Exception as e:
                            logging.warning(f"Could not format deployment time: {e}")
                            model_details["deployment_time"] = str(model.create_time)
                else:
                    raise ValueError("No models could be sorted by creation time")
            else:
                raise ValueError("No deployed models found on the endpoint after multiple retries")
        else:
            # Using specified model ID
            actual_model_id = deployed_model_id
            # Verify this ID exists on the endpoint
            if not any(m.id == actual_model_id for m in deployed_models):
                logging.warning(f"Specified model ID {actual_model_id} not found among deployed models")
        
        # Update the model details with actual model ID
        model_details["deployed_model_id"] = actual_model_id
        
        # List all deployed model IDs for logging
        all_ids = [m.id for m in deployed_models]
        logging.info(f"All deployed model IDs: {all_ids}")
        
        # Prepare the traffic split dictionary
        traffic_split = {}
        
        # Set the traffic percentage for our new model
        traffic_split[actual_model_id] = traffic_percentage
        
        # Distribute remaining traffic (if any) evenly among other deployed models
        remaining_percentage = 100 - traffic_percentage
        other_deployed_models = [
            dm.id for dm in deployed_models 
            if dm.id != actual_model_id
        ]
        
        num_other_models = len(other_deployed_models)
        if num_other_models > 0 and remaining_percentage > 0:
            per_model_percentage = remaining_percentage / num_other_models
            for model_id in other_deployed_models:
                traffic_split[model_id] = per_model_percentage
        
        logging.info(f"Updating traffic split to: {traffic_split}")
        
        # Update the traffic split
        endpoint.update_traffic_split(traffic_split=traffic_split)
        logging.info("Traffic split updated successfully")
        
        # Add information about the traffic split to model details
        model_details["traffic_split"] = json.dumps(traffic_split)
        
    except Exception as e:
        logging.error(f"Error updating traffic split: {e}")
        logging.exception("Full exception details:")
        # Even if there was an error, return the model ID if we found it
    
    outputs = namedtuple("Outputs", ["deployed_model_id", "model_details"])
    return outputs(actual_model_id, model_details) 