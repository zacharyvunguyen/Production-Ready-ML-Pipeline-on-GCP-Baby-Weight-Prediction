from kfp.v2.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform",],
    #output_component_file="src/pipeline/collect_eval_metrics_automl.yaml",
)
def collect_eval_metrics_automl(
    region: str, 
    model: Input[Artifact], 
    metrics: Output[Metrics]
) -> NamedTuple("Outputs",[("metrics_dict", dict),],
):   
    import google.cloud.aiplatform.gapic as gapic
    from collections import namedtuple

    # Get a reference to the Model Service client
    client_options = {"api_endpoint": f"{region}-aiplatform.googleapis.com"}
    model_service_client = gapic.ModelServiceClient(client_options=client_options)

    model_resource_name = model.metadata["resourceName"]
    model_evaluations = model_service_client.list_model_evaluations(parent=model_resource_name)
    model_evaluation = list(model_evaluations)[0]
    available_metrics = [
        "meanAbsoluteError",
        "meanAbsolutePercentageError",
        "rSquared",
        "rootMeanSquaredError",
        "rootMeanSquaredLogError",
    ]
    
    metrics_dict = dict()
    for x in available_metrics:
        val = model_evaluation.metrics.get(x)
        metrics_dict[x] = val
        metrics.log_metric(str(x), float(val))

    metrics.log_metric("framework", "AutoML")
    outputs = namedtuple("Outputs", ["metrics_dict"])
    print(metrics_dict)

    return outputs(metrics_dict)    


