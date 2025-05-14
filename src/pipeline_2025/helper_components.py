from kfp.dsl import Output, component
from typing import NamedTuple

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def construct_vertex_model_resource_name(
    project_id: str,
    region: str,
    vertex_model_id: str,
) -> NamedTuple("Outputs", [("vertex_model_resource_name_str", str)]):
    """Constructs the full Vertex AI Model resource name string."""
    resource_name = f"projects/{project_id}/locations/{region}/models/{vertex_model_id}"
    print(f"Constructed Vertex AI Model Resource Name: {resource_name}")
    return (resource_name,) 