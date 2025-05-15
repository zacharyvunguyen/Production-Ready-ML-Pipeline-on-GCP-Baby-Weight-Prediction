import os
import pandas as pd
import streamlit as st
from google.cloud import aiplatform as vertex_ai
import logging
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union, Tuple
import datetime
import pathlib
import json

# --- Load Environment Variables ---
env_path = pathlib.Path('.env')
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logging.info("Loaded environment variables from .env file")
else:
    logging.warning("No .env file found in the current directory")

# --- Required Environment Variables ---
REQUIRED_ENV_VARS = ["PROJECT"]

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Page Configuration ---
st.set_page_config(
    page_title="👶 Baby Weight Predictor (CI/CD Enabled)",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/username/baby-weight-prediction',
        'Report a bug': 'https://github.com/username/baby-weight-prediction/issues',
        'About': 'This app predicts baby weight using ML models deployed on GCP Vertex AI.'
    }
)

# --- Create Theme Config ---
# This will create the .streamlit folder and config.toml if they don't exist
config_dir = pathlib.Path('.streamlit')
config_dir.mkdir(exist_ok=True)

config_file = config_dir / 'config.toml'
if not config_file.exists():
    config_file.write_text("""
[theme]
primaryColor = "#4F8BF9"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F5FF"
textColor = "#262730"
font = "sans serif"
base = "light"
    """)
    logging.info("Created custom theme configuration")

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stApp {
        background-color: #FAFBFF;
    }
    
    /* Card styles */
    div[data-testid="stForm"] {
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.05);
        background-color: #FFF;
        border: 1px solid #EEF2FF;
    }
    div[data-testid="metric-container"] {
        background-color: #FAFBFF;
        border: 1px solid #E6EFFE;
        border-radius: 0.8rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }
    
    /* Typography */
    h1 {
        color: #1E65F3;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #2E5DE8;
        font-weight: 700;
    }
    h3 {
        color: #4F8BF9;
        font-weight: 600;
    }
    
    /* Alert styles */
    .env-warning {
        padding: 1rem;
        background-color: #FFF5F5;
        border-radius: 0.8rem;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 1rem;
    }
    
    /* Prediction box */
    .prediction-box {
        background-color: #F0F5FF;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        border-left: 5px solid #4F8BF9;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFF;
        border-right: 1px solid #E6EFFE;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #F8FAFF;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.8rem;
        color: #666;
        border-top: 1px solid #E6EFFE;
    }
    
    /* Status indicators */
    .endpoint-active {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10B981;
        margin-right: 6px;
    }
    
    /* Button styles */
    div[data-testid="stButton"] button {
        border-radius: 0.5rem;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Add animation for loading */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .loading {
        animation: pulse 1.5s infinite ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def check_environment_variables() -> bool:
    """
    Check if all required environment variables are set.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    
    if missing_vars:
        st.markdown(
            f"""
            <div class="env-warning">
                <h3>⚠️ Environment Setup Error</h3>
                <p>The following environment variables are required but not set:</p>
                <ul>{"".join([f"<li><code>{var}</code></li>" for var in missing_vars])}</ul>
                <p>Please create or update your <code>.env</code> file with these variables.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def initialize_vertex_ai() -> bool:
    """
    Initialize Vertex AI with the project from environment variables.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Get project ID from environment variable
        project_id = os.getenv("PROJECT")
        region = os.getenv("REGION", "us-central1")
        
        if not project_id:
            logging.error("PROJECT environment variable is required but not set.")
            return False
        
        # Initialize Vertex AI
        vertex_ai.init(project=project_id, location=region)
        logging.info(f"Initialized Vertex AI with project: {project_id}, region: {region}")
        return True
    except Exception as e:
        st.error(f"Failed to initialize Vertex AI: {str(e)}")
        logging.error(f"Vertex AI initialization error: {str(e)}")
        return False

def get_available_endpoints() -> List[Tuple[str, str, datetime.datetime, Optional[str]]]:
    """
    Find all available endpoints for baby weight prediction.
    
    Returns:
        List of tuples containing (endpoint_id, display_name, creation_time, model_id)
    """
    try:
        # List all endpoints
        endpoints = vertex_ai.Endpoint.list()
        
        # Filter endpoints related to baby weight prediction
        relevant_endpoints = [
            endpoint for endpoint in endpoints 
            if any(keyword in endpoint.display_name.lower() for keyword in 
                ["baby", "weight", "natality", "mlops", "pipeline", "babyweight"])
        ]
        
        if not relevant_endpoints:
            logging.warning("No baby weight prediction endpoints found.")
            return []
        
        # Sort by creation time (newest first)
        sorted_endpoints = sorted(
            relevant_endpoints, 
            key=lambda x: x.create_time, 
            reverse=True
        )
        
        endpoint_info = []
        for endpoint in sorted_endpoints:
            model_id = None
            # Get detailed endpoint information
            try:
                # Get a fresh endpoint object to ensure we have the latest data
                endpoint_detail = vertex_ai.Endpoint(endpoint.name)
                endpoint_dict = endpoint_detail.to_dict()
                
                # Try to extract model ID from deployedModels array if it exists
                if "deployedModels" in endpoint_dict and endpoint_dict["deployedModels"]:
                    # Go through each deployed model to find the model ID
                    for deployed_model in endpoint_dict["deployedModels"]:
                        # Try different possible field names for the model ID
                        if "model" in deployed_model and deployed_model["model"]:
                            # Extract last part of the model path 
                            model_path = deployed_model["model"]
                            model_id = model_path.split('/')[-1]
                            break
                        elif "modelId" in deployed_model:
                            model_id = deployed_model["modelId"]
                            break
                        elif "id" in deployed_model:
                            model_id = deployed_model["id"]
                            break
                
                logging.info(f"Found model ID for endpoint {endpoint.display_name}: {model_id}")
            except Exception as e:
                logging.warning(f"Error extracting model ID for endpoint {endpoint.display_name}: {str(e)}")
                model_id = None
            
            endpoint_info.append((
                endpoint.name, 
                endpoint.display_name, 
                endpoint.create_time,
                model_id
            ))
        
        return endpoint_info
    except Exception as e:
        st.error(f"Error finding endpoints: {str(e)}")
        logging.error(f"Endpoint discovery error: {str(e)}")
        return []

def predict_baby_weight(
    is_male: int,
    mother_age: int,
    gestation_weeks: int,
    plurality: int,
    cigarette_use: int,
    alcohol_use: int,
    endpoint_id: str
) -> float:
    """
    Make prediction for baby weight using the Vertex AI endpoint.
    
    Args:
        is_male: 1 if male, 0 if female
        mother_age: Age of the mother in years
        gestation_weeks: Number of gestation weeks
        plurality: Type of pregnancy (1=single, 2=twins, etc.)
        cigarette_use: 1 if the mother smokes, 0 if not
        alcohol_use: 1 if the mother consumes alcohol, 0 if not
        endpoint_id: The Vertex AI endpoint ID to use for prediction
    
    Returns:
        Predicted baby weight in pounds
    """
    try:
        # Create Endpoint instance
        endpoint = vertex_ai.Endpoint(endpoint_id)
        
        # Prepare the instance for prediction
        instance = {
            "is_male": str(is_male),
            "mother_age": str(mother_age), 
            "gestation_weeks": str(gestation_weeks),
            "plurality_category": f"Single({plurality})" if plurality == 1 else f"Multiple({plurality})",
            "cigarette_use_str": "True" if cigarette_use == 1 else "False",
            "alcohol_use_str": "True" if alcohol_use == 1 else "False"
        }
        
        # Log the request (for debugging)
        logging.info(f"Sending prediction request: {instance}")
        
        # Add a little delay for visual effect
        with st.spinner("Getting prediction..."):
            # Make the prediction
            response = endpoint.predict(instances=[instance])
            
            # Extract and validate the prediction
            predictions = response.predictions
            if not predictions or len(predictions) == 0:
                raise ValueError("No predictions returned from the endpoint")
            
            # For debugging
            logging.info(f"Prediction type: {type(predictions[0])}")
            logging.info(f"Prediction content: {predictions[0]}")
            
            # Return the predicted value, handling different response formats
            prediction = predictions[0]
            
            # Case 1: Direct float value
            if isinstance(prediction, (int, float)):
                return float(prediction)
                
            # Case 2: Dictionary with a single value
            elif isinstance(prediction, dict):
                if len(prediction) == 1:
                    # If there's only one value, use it
                    return float(list(prediction.values())[0])
                
                # Try to find a key that might contain the prediction
                for key in ['value', 'prediction', 'result', 'weight', 'output']:
                    if key in prediction:
                        return float(prediction[key])
                
                # If we haven't found a value yet, try to use any numeric value we can find
                for value in prediction.values():
                    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
                        return float(value)
            
            # Case 3: List or array - take first element if it's a number
            elif isinstance(prediction, list) and len(prediction) > 0:
                return float(prediction[0])
            
            # If we reach here, we couldn't parse the prediction
            raise ValueError(f"Could not extract a numeric prediction from the response: {prediction}")
            
    except Exception as e:
        error_msg = f"Prediction error: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def get_weight_category(weight: float) -> Tuple[str, str, str]:
    """
    Categorize baby weight and return status info.
    
    Args:
        weight: Predicted weight in pounds
        
    Returns:
        Tuple of (category, color, message)
    """
    if weight < 5.5:
        return "Low", "warning", "This weight is below the normal range (5.5-8.5 lbs)."
    elif weight > 8.5:
        return "High", "warning", "This weight is above the normal range (5.5-8.5 lbs)."
    else:
        return "Normal", "success", "This weight is within the normal range (5.5-8.5 lbs)."

def format_date(date_obj: datetime.datetime) -> str:
    """Format a datetime object as a readable string"""
    return date_obj.strftime("%b %d, %Y at %H:%M")

# --- App Main ---
def main():
    # Header with logo and title
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image("https://www.gstatic.com/vertex-ai/images/h3-icon.svg", width=70)
    with col2:
        st.title("👶 Baby Weight Predictor")
        st.markdown("""
        This app uses machine learning models deployed on GCP Vertex AI to predict a baby's weight
        based on various maternal and pregnancy factors.
        """)
    
    # Check environment variables before proceeding
    if not check_environment_variables():
        return
    
    # Initialize Vertex AI
    if not initialize_vertex_ai():
        return
    
    # Find available endpoints
    available_endpoints = get_available_endpoints()
    
    if not available_endpoints:
        st.error("⚠️ No available endpoints found for making predictions. The model may not be deployed.")
        st.info("Please run the ML pipeline to deploy a model first.")
        return
    
    # Sidebar for model selection
    st.sidebar.header("🔧 Model Settings")
    
    # Process endpoint options with proper handling for the model ID
    endpoint_options = []
    for endpoint_id, display_name, created_time, model_id in available_endpoints:
        endpoint_options.append({
            "endpoint_id": endpoint_id,
            "display_name": display_name,
            "created_time": created_time
        })
    
    # Ensure endpoint_options is not empty before accessing elements
    if endpoint_options:
        # Automatically select the most recent endpoint (already sorted by create_time)
        selected_endpoint = endpoint_options[0]
        
        # Display endpoint information with status indicator
        st.sidebar.markdown("""
        ### 🔍 Model Information
        """)
        
        # Extract version if it exists in the name
        endpoint_name = selected_endpoint["display_name"]
        version = "latest"
        if '-' in endpoint_name:
            parts = endpoint_name.split('-')
            if len(parts) > 1 and parts[-1].isalnum():
                version = parts[-1]
                
        # Get the endpoint ID for display
        endpoint_id_short = selected_endpoint["endpoint_id"].split('/')[-1]
        
        # Get model ID (from the available_endpoints data)
        model_id = None
        for endpoint_id, display_name, created_time, model_id_value in available_endpoints:
            if endpoint_id == selected_endpoint["endpoint_id"]:
                model_id = model_id_value
                break
        
        # Display model ID if available
        model_id_display = model_id[:10] + "..." if model_id and len(model_id) > 10 else "Not available"
        
        # Create the HTML for the sidebar info box
        sidebar_html = f"""
        <div style="padding: 15px; background-color: #F0F5FF; border-radius: 8px; margin-top: 10px;">
            <div><span class="endpoint-active"></span> <b>Active Endpoint:</b></div>
            <div style="margin-top: 5px; font-size: 0.9rem;">{endpoint_name}</div>
            <div style="margin-top: 5px; font-size: 0.8rem; color: #555;">
                <b>Deployed:</b> {format_date(selected_endpoint["created_time"])}
            </div>
            <div style="margin-top: 10px; font-size: 0.8rem; color: #555; overflow-wrap: break-word;">
                <b>Endpoint ID:</b> {endpoint_id_short}
            </div>
        """
        
        # Only add the model ID section if we have a valid model ID
        if model_id:
            sidebar_html += f"""
            <div style="margin-top: 10px; font-size: 0.8rem; color: #555; overflow-wrap: break-word;">
                <b>Model ID:</b> {model_id}
            </div>
            """
            
        # Close the HTML div
        sidebar_html += """
        </div>
        """
        
        # Display the sidebar info
        st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)
    else:
        st.sidebar.warning("No endpoints available. Please deploy a model first.")
        return
    
    st.sidebar.markdown("---")
    
    # Add model explanation
    with st.sidebar.expander("ℹ️ About the Model"):
        st.markdown("""
        This model was trained using the Natality dataset, which contains information
        on US births from 1969 to 2008. The pipeline uses both BQML and AutoML 
        models, selecting the best performer for deployment.
        
        **Features used:**
        - Baby gender
        - Mother's age
        - Gestation weeks
        - Plurality (single/twins/etc.)
        - Cigarette use
        - Alcohol use
        """)
    
    # Add pipeline explanation
    with st.sidebar.expander("🔄 How the Pipeline Works"):
        st.markdown("""
        **ML Pipeline Steps:**
        - **Data Extraction**: Queries natality data from BigQuery
        - **Data Preparation**: Cleans, transforms, and splits data
        - **Model Training**: Trains both BQML and AutoML models
        - **Model Evaluation**: Compares model performance metrics
        - **Model Selection**: Selects best performing model
        - **Model Registry**: Registers model with versioning
        - **Endpoint Management**: Creates/updates prediction endpoints
        - **Traffic Management**: Controls traffic flow to new models
        
        **Tech Stack:**
        - Google Cloud Vertex AI
        - Kubeflow Pipelines
        - TensorFlow Extended (TFX)
        - BigQuery ML
        """)
    
    # Add CI/CD explanation
    with st.sidebar.expander("🚀 CI/CD Pipeline"):
        st.markdown("""
        **CI/CD Implementation:**
        - **Infrastructure as Code**: Terraform manages all GCP resources
        - **Containerization**: Docker images stored in Artifact Registry
        - **Continuous Integration**: Automated builds via Cloud Build
        - **Continuous Deployment**: Automated deployments to Cloud Run
        - **Environment Separation**: Development and production pipelines
        
        **Deployment Flow:**
        1. Code changes pushed to GitHub repository
        2. Cloud Build trigger detects changes
        3. Docker image built and pushed to Artifact Registry
        4. New version deployed to Cloud Run
        5. Zero-downtime deployment with traffic management
        """)
    
    # Input form with modern styled columns
    with st.form(key="prediction_form", border=True):
        st.subheader("📋 Enter Patient Information")
        
        # Create 3 columns for the first row of inputs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            is_male = st.radio(
                "Baby Gender",
                options=["Male", "Female"],
                horizontal=True,
                help="Select the gender of the baby",
                index=0
            )
            is_male = 1 if is_male == "Male" else 0
        
        with col2:
            mother_age = st.number_input(
                "Mother's Age",
                min_value=12,
                max_value=60,
                value=30,
                step=1,
                help="Enter the mother's age in years"
            )
        
        with col3:
            gestation_weeks = st.number_input(
                "Gestation Weeks",
                min_value=20,
                max_value=45,
                value=40,
                step=1,
                help="Enter the number of weeks of gestation"
            )
        
        # Create 3 columns for the second row of inputs
        col4, col5, col6 = st.columns(3)
        
        with col4:
            plurality_options = {
                1: "Single",
                2: "Twins",
                3: "Triplets",
                4: "Quadruplets",
                5: "Quintuplets"
            }
            plurality_display = st.selectbox(
                "Plurality",
                options=list(plurality_options.values()),
                index=0,
                help="Select the type of pregnancy"
            )
            plurality = [k for k, v in plurality_options.items() if v == plurality_display][0]
        
        with col5:
            cigarette_use = st.radio(
                "Cigarette Use",
                options=["Yes", "No"],
                index=1,
                horizontal=True,
                help="Does the mother smoke cigarettes?"
            )
            cigarette_use = 1 if cigarette_use == "Yes" else 0
        
        with col6:
            alcohol_use = st.radio(
                "Alcohol Use",
                options=["Yes", "No"],
                index=1,
                horizontal=True,
                help="Does the mother consume alcohol?"
            )
            alcohol_use = 1 if alcohol_use == "Yes" else 0
        
        # Submit button
        submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
        with submit_col2:
            submit_button = st.form_submit_button(
                label="🔮 Predict Baby Weight",
                type="primary",
                use_container_width=True
            )
    
    # Make prediction when form is submitted
    if submit_button:
        try:
            # Call the prediction function
            predicted_weight = predict_baby_weight(
                is_male=is_male,
                mother_age=mother_age,
                gestation_weeks=gestation_weeks,
                plurality=plurality,
                cigarette_use=cigarette_use,
                alcohol_use=alcohol_use,
                endpoint_id=selected_endpoint["endpoint_id"]
            )
            
            # Show success toast
            st.toast(f"Prediction successful: {predicted_weight:.2f} lbs", icon="✅")
            
            # Display result in a beautiful section
            st.markdown('<div class="prediction-box">', unsafe_allow_html=True)
            
            # Get weight category and message
            category, status, message = get_weight_category(predicted_weight)
            
            # Display a header with emoji based on category
            emoji_map = {"Low": "⚠️", "Normal": "✅", "High": "⚠️"}
            st.subheader(f"{emoji_map.get(category, '🏆')} Prediction Results")
            
            # Display the prediction in a more visual way
            cols = st.columns([2, 3])
            with cols[0]:
                # Main prediction metric
                st.metric(
                    label="Predicted Weight",
                    value=f"{predicted_weight:.2f} lbs",
                    delta=None
                )
                
                # Display weight in different units
                kg_weight = predicted_weight * 0.453592
                oz_weight = predicted_weight * 16
                st.markdown(f"""
                **In other units:**
                - {kg_weight:.2f} kg
                - {oz_weight:.1f} oz
                """)
            
            with cols[1]:
                # Show normal range info with progress bar
                min_range, max_range = 5.5, 8.5
                st.markdown(f"**Weight Category:** {category}")
                
                # Calculate percentage for progress bar (normalized between min and max weight range)
                progress_range = max_range - min_range
                normalized_weight = min(max(predicted_weight - min_range, 0), progress_range)
                progress_pct = normalized_weight / progress_range
                
                # Display progress bar
                st.progress(progress_pct)
                
                # Display range markers
                cols2 = st.columns(3)
                cols2[0].markdown(f"<div style='text-align: left'>{min_range} lbs</div>", unsafe_allow_html=True)
                cols2[1].markdown(f"<div style='text-align: center'>7.0 lbs</div>", unsafe_allow_html=True)
                cols2[2].markdown(f"<div style='text-align: right'>{max_range} lbs</div>", unsafe_allow_html=True)
                
                # Show status message
                if status == "success":
                    st.success(message)
                else:
                    st.warning(message)
            
            # Display input summary
            st.markdown("### Patient Information Summary")
            
            # Create two columns for the summary
            sum_col1, sum_col2 = st.columns(2)
            
            # Format the data as key-value pairs
            with sum_col1:
                st.markdown(f"**Baby Gender:** {'Male' if is_male == 1 else 'Female'}")
                st.markdown(f"**Mother's Age:** {mother_age} years")
                st.markdown(f"**Gestation Weeks:** {gestation_weeks} weeks")
            
            with sum_col2:
                st.markdown(f"**Plurality:** {plurality_display}")
                st.markdown(f"**Cigarette Use:** {'Yes' if cigarette_use == 1 else 'No'}")
                st.markdown(f"**Alcohol Use:** {'Yes' if alcohol_use == 1 else 'No'}")
            
            # Include risk factors section if applicable
            risk_factors = []
            if cigarette_use == 1:
                risk_factors.append("Cigarette use during pregnancy")
            if alcohol_use == 1:
                risk_factors.append("Alcohol use during pregnancy")
            if gestation_weeks < 37:
                risk_factors.append("Premature birth (< 37 weeks)")
            if plurality > 1:
                risk_factors.append(f"Multiple birth ({plurality_display})")
            
            if risk_factors:
                st.markdown("### Risk Factors")
                for factor in risk_factors:
                    st.markdown(f"- {factor}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error during prediction: {str(e)}")
            logging.error(f"Prediction failed: {str(e)}")
    
    # Add footer with version info
    st.markdown("""
    <div class="footer">
        Version 2.0 | Developed with ❤️ using Streamlit and Vertex AI by Zachary Nguyen | © 2025
    </div>
    """, unsafe_allow_html=True)

# --- App Entry Point ---
if __name__ == "__main__":
    main() 