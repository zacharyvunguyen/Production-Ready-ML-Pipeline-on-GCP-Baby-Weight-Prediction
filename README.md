# Production-Ready ML Pipeline on GCP: Baby Weight Prediction
In this project, I developed a completed Vertex and Kubeflow pipelines SDK to build and deploy an AutoML / BigQuery ML regression model for online predictions. Using this ML Pipeline, I was able to develop, deploy, and manage the _production_ ML lifecycle efficiently and reliably.

* As part of this project, I used the Natality dataset, a public dataset available in BigQuery that provides information on US births from 1969 to 2008. 

* The trained AutoML/BQML models predicted the weight of newborns. The predicted values would be used in order to provide care for the newborns.

* The pipeline features two parallel branches - one for BQML and one for AutoML - allowing comparison between both approaches.

* At the end, a streamlit application is then created to show how the model can interact with a web application to provide online predictions.

## Streamlit App for Online Predictions
![](img/demo.gif)

## Vertex AI Pipeline Structure
---------------------
![](img/Full_Pipeline.png)

## Key Improvements

The pipeline includes several performance and reliability improvements:

1. **Parallel Model Training**: The pipeline trains both BigQuery ML and AutoML models simultaneously, allowing for performance comparison.

2. **Robust Metrics Collection**: 
   - Implemented timeout mechanisms to prevent components from hanging
   - Added comprehensive error handling for API interactions
   - Standardized metric outputs between BQML and AutoML components

3. **Efficient Caching**: Modified components to properly leverage Vertex Pipeline caching, ensuring that only affected steps run when inputs change.

4. **Consistent Error Handling**: All components handle errors gracefully and provide meaningful logs.

## Technical Architecture

The pipeline follows these stages:

1. **Data Preparation**: Extract and preprocess data from BigQuery
2. **Model Training**: Train both BQML and AutoML models in parallel
3. **Model Evaluation**: Evaluate models and collect standardized metrics
4. **Metrics Collection**: Extract and store evaluation metrics for both models

The improved AutoML metrics collection component ensures reliable extraction of:
- Mean Absolute Error (MAE)
- Mean Squared Error (MSE) 
- Root Mean Squared Error (RMSE)
- R-squared (R²)

See `pipeline.md` for detailed documentation on each component.


