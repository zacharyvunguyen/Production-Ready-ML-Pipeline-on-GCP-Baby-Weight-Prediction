# Production-Ready ML Pipeline on GCP: Baby Weight Prediction
This project showcases a production-ready ML pipeline using Vertex AI and Kubeflow Pipelines SDK to build, train, evaluate, and deploy machine learning models for baby weight prediction. The pipeline delivers a complete MLOps solution with robust model governance, intelligent deployment, and operational excellence.

* Using the Natality dataset, a public dataset available in BigQuery that provides information on US births from 1969 to 2008.

* The trained AutoML/BQML models predict the weight of newborns, with potential applications in healthcare for providing appropriate care for newborns.

* The pipeline features two parallel branches - one for BQML and one for AutoML - allowing comparison between both approaches.

* A model selection component automatically chooses the best-performing model based on configurable metrics and thresholds.

* A Streamlit web application demonstrates how the deployed model can be used for online predictions.

## Streamlit App for Online Predictions
![](img/demo.gif)

## Vertex AI Pipeline Structure
---------------------
![](img/Full_Pipeline.png)

## Key Features

The pipeline includes several production-ready features:

1. **Parallel Model Training**: Trains both BigQuery ML and AutoML models simultaneously, enabling performance comparison and framework diversity.

2. **Intelligent Model Selection**:
   - Automatically compares model performance using configurable metrics
   - Supports both "lower is better" metrics (MAE, RMSE) and "higher is better" metrics (R²)
   - Makes deployment decisions based on customizable thresholds

3. **Endpoint Management**:
   - Checks for existing endpoints before creating new ones
   - Prevents endpoint proliferation in production environments
   - Simplifies maintenance and reduces resource usage

4. **Model Registry Integration**:
   - Registers models with comprehensive metadata
   - Tracks model lineage and version history
   - Enables governance and compliance capabilities

5. **Traffic Management**:
   - Supports gradual traffic shifting to new model versions
   - Enables blue/green deployment strategies
   - Minimizes disruption during model updates

6. **Efficient Caching**: Leverages Vertex Pipeline caching to optimize resource usage and development speed.

7. **Robust Error Handling**: All components include comprehensive error handling and detailed logging.

## Technical Architecture

The pipeline follows these stages:

1. **Data Preparation**: Extract and preprocess data from BigQuery
2. **Model Training**: Train both BQML and AutoML models in parallel
3. **Model Evaluation**: Evaluate models and collect standardized metrics
4. **Model Selection**: Compare models and select the best performer
5. **Model Registration**: Register the selected model with metadata
6. **Endpoint Management**: Create or reuse endpoints for deployment
7. **Deployment**: Deploy the model with appropriate resources
8. **Traffic Management**: Route traffic to the new model version

The pipeline uses a dual approach for endpoints:
- A standard component (`EndpointCreateOp`) for compatibility
- An enhanced component (`get_or_create_endpoint`) for avoiding duplication

See `pipeline.md` for detailed documentation on each component.

## Benefits for Production Environments

This ML pipeline delivers significant benefits for production ML operations:

1. **Resource Efficiency**: Prevents endpoint proliferation and optimizes resource usage
2. **Operational Excellence**: Simplified maintenance with fewer endpoints to manage
3. **Governance**: Comprehensive model registry integration with metadata tracking
4. **Reliability**: Graceful handling of deployment transitions with traffic management
5. **Development Speed**: Efficient caching and parallel training for faster iterations
6. **Quality Control**: Deployment thresholds ensure only models meeting quality standards are deployed


