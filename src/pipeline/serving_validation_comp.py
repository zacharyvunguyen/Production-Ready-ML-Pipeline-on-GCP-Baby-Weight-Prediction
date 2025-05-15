import sys
import os
from kfp.v2.dsl import Artifact, Input, Metrics, Model, Output, component
from typing import NamedTuple

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform",],
    output_component_file="src/pipeline/validate_serving.yaml",
)
def validate_serving(
    endpoint: Input[Artifact],
) -> NamedTuple(
    "Outputs", [("instance", str), ("prediction", float)]
):
    import logging
    import json
    from collections import namedtuple

    from google.cloud import aiplatform
    from google.protobuf import json_format
    from google.protobuf.struct_pb2 import Value

    def treat_uri(uri):
        return uri[uri.find("projects/") :]

    def request_prediction(endp, instance):
        instance = json_format.ParseDict(instance, Value())
        instances = [instance]
        parameters_dict = {}
        parameters = json_format.ParseDict(parameters_dict, Value())
        response = endp.predict(instances=instances, parameters=parameters)
        logging.info("deployed_model_id:", response.deployed_model_id)
        logging.info("predictions: ", response.predictions)
        # The predictions are a google.protobuf.Value representation of the model's predictions.
        predictions = response.predictions

        for pred in predictions:
            if type(pred) is dict and "value" in pred.keys():
                # AutoML predictions
                prediction = pred["value"]
            elif type(pred) is list:
                # BQML predictions 
                prediction = pred[0]
            return prediction

    endpoint_uri = endpoint.uri
    treated_uri = treat_uri(endpoint_uri)

    instance = {
        "num_proc_codes": 1.0,
        "patient_age_yrs": 18,
        "patient_bmi_group": "Normalweight",
        "patient_type_group": "OUTPATIENT",
        "primary_procedure_code": "11772",
    }
    instance_json = json.dumps(instance)
    logging.info("Will use the following instance: " + instance_json)

    endpoint = aiplatform.Endpoint(treated_uri)
    prediction = request_prediction(endpoint, instance)
    result_tuple = namedtuple("Outputs", ["instance", "prediction"])

    return result_tuple(instance=str(instance_json), prediction=float(prediction))