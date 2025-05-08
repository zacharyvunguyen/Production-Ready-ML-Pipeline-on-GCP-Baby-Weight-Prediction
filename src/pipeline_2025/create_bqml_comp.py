from kfp.dsl import Artifact, Input, Metrics, Output, component
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
        MAX_PARALLEL_TRIALS = 4,
        NUM_TRIALS = 24
        ) AS
    SELECT * EXCEPT(data_split),
        CASE
            WHEN data_split = 'VALIDATE' THEN 'EVAL'
            ELSE data_split
        END AS custom_splits
    FROM `{bq_train_table_id}`
    """
    
    return query




@component(
    base_image="python:3.10",
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
    metrics_dict = {}
    rmse = None
    
    if not metadata or 'rows' not in metadata or not metadata['rows']:
        print("Warning: Evaluation metrics artifact metadata is empty or missing 'rows'.")
        outputs = namedtuple("Outputs", ["metrics_dict"])
        return outputs({})

    try:
        schema = metadata["schema"]["fields"]
        rows = metadata["rows"][0]["f"]
        
        for metric, value in zip(schema, rows):
            metric_name = metric["name"]
            try:
                val = float(value["v"])
                metrics_dict[metric_name] = val
                metrics.log_metric(metric_name, val)
                if metric_name == "mean_squared_error":
                    rmse = math.sqrt(val)
                    metrics.log_metric("root_mean_squared_error", rmse)
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not convert metric '{metric_name}' value '{value['v']}' to float: {e}")

    except (KeyError, IndexError) as e:
        print(f"Error parsing metrics artifact metadata: {e}. Metadata structure might be different.")
        outputs = namedtuple("Outputs", ["metrics_dict"])
        return outputs({})

    metrics.log_metric("framework", "BQML")
    print(f"Collected metrics_dict: {metrics_dict}")
    
    outputs = namedtuple("Outputs", ["metrics_dict"])

    return outputs(metrics_dict)
