from kfp.v2.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple

def create_query_build_bqml_model(
    project: str,
    bq_dataset: str,
    bq_model_name: str,
    bq_version_aliases: str,
    var_target: str,
    bq_train_table_id: str, 
):
    bq_model_id = f"{project}.{bq_dataset}.{bq_model_name}"
    query = f"""
    CREATE MODEL IF NOT EXISTS `{bq_model_id}`
    OPTIONS(
        model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
        model_registry = 'vertex_ai', 
        vertex_ai_model_version_aliases = ['{bq_version_aliases}'],
        input_label_cols = ['{var_target}'],
        data_split_col = 'custom_splits',
        data_split_method = 'CUSTOM',
        HIDDEN_UNITS = [256, 128, 64],
        OPTIMIZER = 'adagrad',
        BATCH_SIZE = HPARAM_CANDIDATES([16, 32, 64]),
        DROPOUT =  HPARAM_CANDIDATES([0, 0.1, 0.2]),
        MAX_ITERATIONS = 5,
        MAX_PARALLEL_TRIALS = 2,
        NUM_TRIALS = 2
        ) AS
    SELECT * EXCEPT(splits),
        CASE
            WHEN splits = 'VALIDATE' THEN 'EVAL'
            ELSE splits
        END AS custom_splits
    FROM `{bq_train_table_id}`
    """
    
    return query




@component(
    base_image="python:3.9",
    #output_component_file="src/pipeline/collect_eval_metrics_bqml.yaml",
)
def collect_eval_metrics_bqml(
    eval_metrics_artifact: Input[Artifact],
    metrics: Output[Metrics],
) -> NamedTuple(
    "Outputs",[
        #("metrics", Output[Metrics]),
        ("metrics_dict", dict),],
):    

    import math
    from collections import namedtuple

    metadata = eval_metrics_artifact.metadata
    for r in metadata["rows"]:
        rows = r["f"]
        schema = metadata["schema"]["fields"]
        metrics_dict = {}
        for metric, value in zip(schema, rows):
            metric_name = metric["name"]
            val = float(value["v"])
            metrics_dict[metric_name] = val
            metrics.log_metric(metric_name, val)
            if metric_name == "mean_squared_error":
                rmse = math.sqrt(val)
                metrics.log_metric("root_mean_squared_error", rmse)

    metrics.log_metric("framework", "BQML")

    print(metrics_dict)
    
    outputs = namedtuple("Outputs", 
                         [#"metrics", 
                          "metrics_dict"])

    return outputs(
        #metrics,
        metrics_dict)
