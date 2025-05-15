# -*- coding: utf-8 -*-
"""
Author: Zachary Nguyen
"""

import streamlit as st
from streamlit_option_menu import option_menu
import os
from tabulate import tabulate
import numpy as np
from google.cloud import aiplatform as aip
from google.cloud import bigquery
import pandas as pd

######################################
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



################################
# config
st.set_page_config(
    page_title="Zachary",
    page_icon="🧊",
    layout="wide",

)
# sidebar for navigation
with st.sidebar:
    selected = option_menu('Zachary Nguyen',

                           ['Surgery Duration Prediction','Home'],
                           icons=['heart', 'house'],
                           default_index=0)

# Home Page
if (selected == 'Home'):
    # page title
    st.title('Home')

# Zachary Heart Disease Classification
if (selected == 'Surgery Duration Prediction'):

    # page title
    st.title('Surgery Duration Prediction')
    #col1, col2 = st.columns([1, 3])
    #with col1:
    st.image('img/img.png', width=200)

    # getting the input data from the user
    col1, col2, col3 = st.columns([1, 2, 2])

    #### VARIABLES
    #normalized_surgeon_specialty_name = pd.read_csv("data/normalized_surgeon_specialty_name.csv")
    #list_ss_name = normalized_surgeon_specialty_name[
    #    'normalized_surgeon_specialty_name'].tolist()

    ###**********INPUT VARIABLES*******************
    with col2:
        is_male = st.selectbox('Is the baby gender male?',['true','false'])
        #st.write('Surgeon specialty name is ', normalized_surgeon_specialty_name)

    with col2:
        #mother_age = st.text_input('What is the age of the mother?')
        mother_age = st.slider('What is the age of the mother?', 10, 100, 25)
        #st.write('Primary procedure code is ', primary_procedure_code)

    with col2:
        plurality = st.selectbox('How many children were born as a result of this pregnancy?',
                                      ['single(1)', 'Twins(2)', 'Triplets(3)','Quadruplets(4)'])
        #st.write('Num Proc Codes is ', num_proc_codes)

    with col3:
        #gestation_weeks = st.text_input('The number of weeks of the pregnancy:')
        gestation_weeks = st.slider('The number of weeks of the pregnancy:', 10, 50, 37)

    with col3:
        cigarette_use = st.selectbox('If the mother  mnjhsmoked cigarettes?',['true','false'])

    with col3:
        alcohol_use = st.selectbox('If the mother drinked alcohol?',['true','false'])


    ########################INPUT DATA ARRAY#################
    input_data = (is_male,mother_age,plurality,gestation_weeks,
                  cigarette_use,alcohol_use)
    #with col1:
    #    st.caption(input_data)

    s = [
        {'is_male': is_male,
         'mother_age': str(mother_age),
         'plurality': plurality,
         'gestation_weeks': str(gestation_weeks),
         'cigarette_use': cigarette_use,
         'alcohol_use': alcohol_use,
         },
    ]

    # code for Prediction
    final_message = ''

    # creating a button for Prediction
    with col1:
        if st.button("Baby weight prediction"):
            predicted_value = endpoint.predict(s).predictions[0]['value']
            st.metric(label='Surgical Prediction Time', value=predicted_value)
            st.balloons()


