from google.cloud import aiplatform
import json

# Initialize the Vertex AI SDK
aiplatform.init(project="baby-mlops", location="us-central1")

# Get the latest pipeline job ID (update this if you run again)
pipeline_job_id = "baby-mlops-pipeline-data-prep-only-20250507213406"
pipeline_job = aiplatform.PipelineJob.get(
    f'projects/526740145114/locations/us-central1/pipelineJobs/{pipeline_job_id}'
)

print(f"Pipeline Job Name: {pipeline_job.display_name}")
print(f"Pipeline Job State: {pipeline_job.state}")
print(f"Pipeline Create Time: {pipeline_job.create_time}")

# Access pipeline run info through the Google Cloud API client
api_client = aiplatform.gapic.PipelineServiceClient(
    client_options={"api_endpoint": f"{pipeline_job.location}-aiplatform.googleapis.com"}
)

# Get detailed pipeline job info
request = aiplatform.gapic.GetPipelineJobRequest(
    name=f"projects/526740145114/locations/{pipeline_job.location}/pipelineJobs/{pipeline_job_id}"
)
response = api_client.get_pipeline_job(request=request)

print("\nPipeline Job Artifacts:")
if hasattr(response, "runtime_config") and hasattr(response.runtime_config, "output_artifacts"):
    for name, artifact in response.runtime_config.output_artifacts.items():
        print(f"  {name}: {artifact}")

print("\nExtracting task outputs and execution details:")
# Go through all the tasks, especially the extract_source_data and preprocess_data_and_split
if response.job_detail and response.job_detail.task_details:
    for task_detail in response.job_detail.task_details:
        task_name = task_detail.task_name
        print(f"\nTask: {task_name}")
        print(f"  Execution ID: {task_detail.execution.name if task_detail.execution else 'N/A'}")
        print(f"  State: {task_detail.state}") # Look for state indicating CACHED (often specific enum value)
        print(f"  Create Time: {task_detail.create_time}")
        print(f"  Start Time: {task_detail.start_time}")
        print(f"  End Time: {task_detail.end_time}")
        
        # Calculate duration if possible
        if task_detail.start_time and task_detail.end_time:
            duration = task_detail.end_time - task_detail.start_time
            print(f"  Duration: {duration}")
        else:
            print("  Duration: N/A (task might not have run or times missing)")
        
        # Print outputs, if available
        if hasattr(task_detail, "outputs") and task_detail.outputs:
            print("  Task Outputs:")
            for key, value in task_detail.outputs.items():
                print(f"    {key}: {value}")
        
        # Check for artifact outputs
        # (Code for checking artifacts was here, keeping it minimal for clarity on caching)
else:
    print("No task details found in the pipeline job response.")

# Check the BigQuery tables directly to confirm their existence
print("\nChecking BigQuery tables directly:")
from google.cloud import bigquery

bq_client = bigquery.Client(project="baby-mlops")
try:
    # Use the fixed table names
    extracted_table_ref = bigquery.TableReference.from_string(
        "baby-mlops.baby_mlops_data_staging.natality_source_extract"
    )
    extracted_table = bq_client.get_table(extracted_table_ref)
    print(f"Extracted table exists: {extracted_table_ref.path}")
    print(f"  Row count: {extracted_table.num_rows}")
    # print(f"  Schema:") # Keep output concise
    # for field in extracted_table.schema[:10]:
    #     print(f"    {field.name}: {field.field_type}")
except Exception as e:
    print(f"Error checking extracted table: {e}")

try:
    # Use the fixed table names
    prepped_table_ref = bigquery.TableReference.from_string(
        "baby-mlops.baby_mlops_data_staging.natality_features_prepped"
    )
    prepped_table = bq_client.get_table(prepped_table_ref)
    print(f"Prepped table exists: {prepped_table_ref.path}")
    print(f"  Row count: {prepped_table.num_rows}")
    # print(f"  Schema:") # Keep output concise
    # for field in prepped_table.schema[:10]:
    #     print(f"    {field.name}: {field.field_type}")
except Exception as e:
    print(f"Error checking prepped table: {e}") 