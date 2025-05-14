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
) -> NamedTuple("Outputs", [("success", bool)]):
    """Updates traffic split for a deployed model on an endpoint.
    
    Args:
        project_id: The GCP project ID
        location: The GCP region
        endpoint_resource_name: The full resource name of the endpoint
        deployed_model_id: ID of the deployed model to direct traffic to, or "PLACEHOLDER_ID" to use the most recently deployed model
        traffic_percentage: Percentage of traffic to route to the model (0-100)
        
    Returns:
        success: Whether the traffic update was successful
    """
    import logging
    from google.cloud import aiplatform
    from collections import namedtuple
    import time
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Vertex AI SDK
    aiplatform.init(project=project_id, location=location)
    
    # Get the endpoint
    logging.info(f"Retrieving endpoint: {endpoint_resource_name}")
    endpoint = aiplatform.Endpoint(endpoint_name=endpoint_resource_name)
    
    # Get current deployed models
    try:
        # Wait a bit to ensure model deployment is completed
        logging.info("Waiting for model deployment to complete...")
        time.sleep(30)
        
        # Refresh endpoint information
        endpoint = aiplatform.Endpoint(endpoint_name=endpoint_resource_name)
        
        # Get the real model ID if a placeholder was provided
        actual_model_id = deployed_model_id
        if deployed_model_id == "PLACEHOLDER_ID":
            # If using placeholder, get the most recently deployed model
            if endpoint.gca_resource.deployed_models:
                # Sort deployed models by deployment time (most recent first)
                sorted_models = sorted(
                    endpoint.gca_resource.deployed_models, 
                    key=lambda m: m.create_time.seconds if hasattr(m, 'create_time') else 0,
                    reverse=True
                )
                actual_model_id = sorted_models[0].id
                logging.info(f"Using most recently deployed model with ID: {actual_model_id}")
            else:
                logging.error("No deployed models found on the endpoint")
                success = False
                outputs = namedtuple("Outputs", ["success"])
                return outputs(success)
        
        # Prepare the traffic split dictionary
        traffic_split = {}
        
        # Set the traffic percentage for our new model
        traffic_split[actual_model_id] = traffic_percentage
        
        # Distribute remaining traffic (if any) evenly among other deployed models
        remaining_percentage = 100 - traffic_percentage
        other_deployed_models = [
            dm.id for dm in endpoint.gca_resource.deployed_models 
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
        success = True
    except Exception as e:
        logging.error(f"Error updating traffic split: {e}")
        success = False
    
    outputs = namedtuple("Outputs", ["success"])
    return outputs(success) 