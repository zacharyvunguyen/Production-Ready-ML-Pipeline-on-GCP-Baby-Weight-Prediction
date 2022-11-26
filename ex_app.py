#!pip install ipython-autotime
#%load_ext autotime
import os
from tabulate import tabulate
import numpy as np
from google.cloud import aiplatform as aip
from google.cloud import bigquery
import pandas as pd
import streamlit as st

####################
NOTEBOOK ='Vertex_AI_Streamlit'
REGION = "us-central1"
PROJECT = 'babyweight-prediction'
BUCKET = 'b_w_bucket'
BQ_DATASET = "bw_dataset"
APPNAME = "bw-prediction"
GOOGLE_APPLICATION_CREDENTIALS = 'key/babyweight-prediction-ff79f406c099.json'

os.environ["REGION"] = REGION
os.environ["PROJECT"] = PROJECT
os.environ["BUCKET"] = BUCKET
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
GCS_BUCKET=f"gs://{BUCKET}"
######################
aip.init(
    project=PROJECT,
    location=REGION,
    staging_bucket=GCS_BUCKET)

ENDPOINT_NAME = 'projects/69318036822/locations/us-central1/endpoints/4074389870305345536'

endpoint = aip.Endpoint(
    project=PROJECT,
    location=REGION,
    endpoint_name=ENDPOINT_NAME
)
########################
# config
st.set_page_config(
    page_title="Zachary",
    page_icon="🧊",
    layout="wide",
)

#*************SIDEBAR*************#
with st.sidebar:
    st.title('Surgery Duration Prediction')
    #Input:
    is_male = st.selectbox('What is the gender of the baby?',['Boy','Girl'])
    mother_age = st.slider('What is the age of the mother?', 10, 100, 25)
    plurality = st.selectbox('How many children were born as a result of this pregnancy?',
                             ['single(1)', 'Twins(2)', 'Triplets(3)','Quadruplets(4)'])
    gestation_weeks = st.slider('The number of weeks of the pregnancy:', 10, 50, 37)
    cigarette_use = st.selectbox('Maternal smoking status:',['Yes','No'])
    alcohol_use = st.selectbox('Maternal drinking status:',['Yes','No'])

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Baby Gender", is_male.upper())
col2.metric("Mother Age", mother_age)
col3.metric("Plurality", plurality.upper())
col4.metric("Gestation Week Number", gestation_weeks)
col5.metric("Maternal smoking status", cigarette_use.upper())
col6.metric("Maternal drinking status", alcohol_use.upper())



#*************GENERATE INPUT*************#
if is_male =='Boy':
    is_male = 'true'
else:
    is_male = 'false'

if cigarette_use =='Yes':
    is_male = 'true'
else:
    is_male = 'false'

if alcohol_use =='Yes':
    is_male = 'true'
else:
    is_male = 'false'

instance = [
    {'is_male': is_male,
     'mother_age': str(mother_age),
     'plurality': plurality,
     'gestation_weeks': str(gestation_weeks),
     'cigarette_use': cigarette_use,
     'alcohol_use': alcohol_use,
     },
]
#*************GENERATE RESULT*************#
predicted_value = ''

with st.sidebar:
    if st.button("Baby weight prediction"):
        predicted_value = round(endpoint.predict(instance).predictions[0]['value'],2)
        st.balloons()

st.metric(label='Surgical Prediction Time', value=f"{predicted_value} LB")

#*************EXPLAINATION RESULT*************#
col1, col2 = st.columns(2)
with col1:
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=["a", "b", "c"])
    st.area_chart(chart_data)

with col2:
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=["a", "b", "c"])
    st.area_chart(chart_data)