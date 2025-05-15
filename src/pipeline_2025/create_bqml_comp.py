from kfp.dsl import Artifact, Input, Metrics, Output, component
from typing import NamedTuple

def create_query_build_bqml_model(
    project: str,
    bq_dataset: str,
    bq_model_name: str,
    formatted_bq_version_aliases: str,
    var_target: str,
    bq_train_table_id: str,
    model_registry: str = None,
    vertex_ai_model_id: str = None,
):
    bq_model_id = f"{project}.{bq_dataset}.{bq_model_name}"

    # The formatted_bq_version_aliases is now expected to be like "['v1', 'latest']"
    # No need to split and re-join here.

    # Build options, starting with the standard ones
    options = [
        "model_type = 'DNN_LINEAR_COMBINED_REGRESSOR'",
        f"vertex_ai_model_version_aliases = {formatted_bq_version_aliases}",
        f"input_label_cols = ['{var_target}']",
        "data_split_col = 'custom_splits'",
        "data_split_method = 'CUSTOM'",
        "HIDDEN_UNITS = [256, 128, 64]",
        "OPTIMIZER = 'adagrad'",
        "BATCH_SIZE = HPARAM_CANDIDATES([16, 32, 64])",
        "DROPOUT =  HPARAM_CANDIDATES([0, 0.1, 0.2])",
        "MAX_ITERATIONS = 5",
        "MAX_PARALLEL_TRIALS = 4",
        "NUM_TRIALS = 24"
    ]
    
    # Add Vertex AI registration options if specified
    if model_registry:
        options.insert(1, f"model_registry = '{model_registry}'")
        
    if vertex_ai_model_id:
        options.insert(2, f"vertex_ai_model_id = '{vertex_ai_model_id}'")

    # Join all options with commas and newlines for readability
    options_str = ",\n        ".join(options)

    query = f"""
    CREATE MODEL IF NOT EXISTS `{bq_model_id}`
    OPTIONS(
        {options_str}
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
    'outputs',[
        ("mean_absolute_error", float),
        ("mean_squared_error", float),
        ("root_mean_squared_error", float),
        ("r2_score", float),
        ("median_absolute_error", float),
        ("framework", str)
    ]
):    
    """Parses BQML evaluation metrics artifact and returns key metrics individually."""
    import math
    from collections import namedtuple
    import json # For printing the full dict if needed

    metadata = eval_metrics_artifact.metadata
    metrics_dict = {}
    # Initialize metrics with default values (e.g., NaN or specific error value)
    mae = float('nan')
    mse = float('nan')
    rmse = float('nan')
    r2 = float('nan') 
    med_ae = float('nan')
    framework = "BQML"
    
    if not metadata or 'rows' not in metadata or not metadata['rows']:
        print("Warning: Evaluation metrics artifact metadata is empty or missing 'rows'. Returning NaN metrics.")
        # Return default/NaN values if metrics can't be parsed
        Outputs = namedtuple('outputs', ["mean_absolute_error", "mean_squared_error", "root_mean_squared_error", "r2_score", "median_absolute_error", "framework"])
        return Outputs(mean_absolute_error=mae, mean_squared_error=mse, root_mean_squared_error=rmse, r2_score=r2, median_absolute_error=med_ae, framework=framework)

    # Assuming the structure based on typical BQML EVALUATE output
    try:
        schema = metadata["schema"]["fields"]
        # Expecting only one row of results from ML.EVALUATE
        rows = metadata["rows"][0]["f"]
        
        raw_metrics = {}
        for metric, value in zip(schema, rows):
            raw_metrics[metric["name"]] = value["v"] # Store raw values first
            
        print(f"Raw metrics extracted: {json.dumps(raw_metrics)}")

        # Safely extract and convert known metrics
        def safe_get_float(metric_name):
            try:
                return float(raw_metrics.get(metric_name))
            except (ValueError, TypeError, KeyError):
                print(f"Warning: Could not parse or find metric '{metric_name}'.")
                return float('nan')

        mae = safe_get_float("mean_absolute_error")
        mse = safe_get_float("mean_squared_error")
        r2 = safe_get_float("r2_score")
        med_ae = safe_get_float("median_absolute_error")

        # Log all extracted metrics to KFP Metrics
        metrics.log_metric("mean_absolute_error", mae)
        metrics.log_metric("mean_squared_error", mse)
        metrics.log_metric("r2_score", r2)
        metrics.log_metric("median_absolute_error", med_ae)

        if not math.isnan(mse):
            rmse = math.sqrt(mse)
            metrics.log_metric("root_mean_squared_error", rmse)
        else:
            metrics.log_metric("root_mean_squared_error", float('nan'))
            rmse = float('nan')
        
        metrics.log_metric("framework", framework)

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing metrics artifact metadata: {e}. Metadata structure might be different. Returning NaN metrics.")
        # Fallback to default/NaN values on parsing error
        Outputs = namedtuple('outputs', ["mean_absolute_error", "mean_squared_error", "root_mean_squared_error", "r2_score", "median_absolute_error", "framework"])
        return Outputs(mean_absolute_error=mae, mean_squared_error=mse, root_mean_squared_error=rmse, r2_score=r2, median_absolute_error=med_ae, framework=framework)

    print(f"Processed Metrics - MAE: {mae}, MSE: {mse}, RMSE: {rmse}, R2: {r2}, MedAE: {med_ae}")
    
    # Define the output tuple structure again before returning
    Outputs = namedtuple('outputs', ["mean_absolute_error", "mean_squared_error", "root_mean_squared_error", "r2_score", "median_absolute_error", "framework"])

    # Return individual metrics
    return Outputs(
        mean_absolute_error=mae, 
        mean_squared_error=mse, 
        root_mean_squared_error=rmse, 
        r2_score=r2,
        median_absolute_error=med_ae,
        framework=framework
    )
