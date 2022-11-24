import sys
import os
from kfp.v2.dsl import Artifact, Input, Metrics, Model, Output, component
from typing import NamedTuple

@component(
    base_image="python:3.9",
    output_component_file="src/pipeline/select_best_model.yaml",
)
def select_best_model(
    automl_metrics: Input[Metrics],
    automl_model: Input[Artifact],
    bqml_metrics: Input[Metrics],
    bqml_model: Input[Artifact],
    
    #custom_model_metrics: Input[Metrics],
    reference_metric_name: str,
    thresholds_dict: dict,
    best_model_metrics: Output[Metrics], 
    best_model: Output[Artifact],
) -> NamedTuple(
    "Outputs",[
        ("deploy_decision", str),
        ("best_model_name", str),
        ("best_metric", float),
    ],
):
    import logging
    import json
    from collections import namedtuple

    # In cases where the models use different metrics
    if reference_metric_name == "mae":
        metric_possible_names = ["meanAbsoluteError", "mean_absolute_error","mae"]
    elif reference_metric_name == "mse":
        metric_possible_names = ["MeanSquaredError", "mean_squared_error", "mse"]
        
    logging.info(f"automl_metrics.metadata: {automl_metrics.metadata}")
    logging.info(f"bqml_metrics.metadata: {bqml_metrics.metadata}")
    #logging.info(f"custom_model_metrics.metadata: {custom_model_metrics.metadata}")
    
    for metric_name in metric_possible_names:     
        try:
            automl_metric = automl_metrics.metadata[metric_name]
            logging.info(f"automl_metric: {automl_metrics}")
        except:
            logging.info(f"{metric_name} does not exist in the AutoML Model dictionary")
            
        try:
            bqml_metric = bqml_metrics.metadata[metric_name]
            logging.info(f"bqml_metric: {bqml_metric}")
        except:
            logging.info(f"{metric_name} does not exist in the BQML dictionary")

        #try:
        #    custom_model_metric = custom_model_metrics.metadata[metric_name]
        #    logging.info(f"custom_model_metric: {custom_model_metric}")
        #except:
        #    logging.info(f"{metric_name} does not exist in the Custom Model dictionary")

    # Find the best model (i.e. with the smallest RMSE)
    if bqml_metric <= automl_metric:
        best_model_name = "bqml"
        best_model = bqml_model
        best_metric = bqml_metric
        best_model_metrics.metadata = bqml_metrics.metadata
    else:
        best_model_name = "automl"
        best_model = automl_model
        best_metric = automl_metric
        best_model_metrics.metadata = automl_metrics.metadata

    # Determine if the best model meets the threshold
    if best_metric < thresholds_dict[reference_metric_name]:
        deploy_decision = "true"
    else:
        deploy_decision = "false"

    logging.info(f"Which model is best? {best_model_name}")
    logging.info(f"What metric is being used? {reference_metric_name}")
    logging.info(f"What is the best metric? {best_metric}")
    logging.info(f"What is the threshold to deploy? {thresholds_dict}")
    logging.info(f"Deploy decision: {deploy_decision}")

    outputs = namedtuple(
        "Outputs", ["deploy_decision", "best_model_name", "best_metric",]
    )

    return outputs(deploy_decision, best_model_name, best_metric)

