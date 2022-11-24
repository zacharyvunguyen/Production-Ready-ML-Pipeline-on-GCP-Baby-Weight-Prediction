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

ENDPOINT_NAME = 'projects/157478440416/locations/us-central1/endpoints/8601070445766115328'

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
    st.image('img/img.png', width=300)

    # getting the input data from the user
    col1, col2, col3 = st.columns([1, 2, 2])

    #### VARIABLES
    normalized_surgeon_specialty_name = pd.read_csv("data/normalized_surgeon_specialty_name.csv")
    list_ss_name = normalized_surgeon_specialty_name[
        'normalized_surgeon_specialty_name'].tolist()

    ###**********INPUT VARIABLES*******************
    with col2:
        normalized_surgeon_specialty_name = st.selectbox('Surgeon specialty name:(Ex: Orthopedic Surgery)',list_ss_name)
        #st.write('Surgeon specialty name is ', normalized_surgeon_specialty_name)

    with col2:
        primary_procedure_code = st.text_input('Primary procedure code (Ex: 11042)')
        #st.write('Primary procedure code is ', primary_procedure_code)

    with col2:
        diagnosis_1 = st.text_input('Diagnosis (Ex: T81.89XA)')
        #st.write('Diagnosis is ', diagnosis_1)

    with col2:
        num_proc_codes = st.selectbox('Num Proc Codes',
                                      ['1', '2', '3','4','5','6'])
        #st.write('Num Proc Codes is ', num_proc_codes)

    with col2:
        hosp_health_ministry = st.selectbox('Hospital health ministry',['MIGRA','TNNAS'])
        #st.write('Hospital health ministry is ', hosp_health_ministry)

    with col3:
        patient_type_group = st.selectbox('Patient type group',['OUTPATIENT','SAME DAY SURGERY',
                                                                'INPATIENT','OBSERVATION'])
        #st.write('Patient type group ', patient_type_group)

    with col3:
        num_diag_codes = st.selectbox('Diag code',
                                      ['1', '2', '3','4','5','6','7','8','9','10','11','12','13','14',
                                       '15'])
        #st.write('Diag code ', num_diag_codes)

    with col3:
        patient_gender = st.radio('Patient gender (Ex: M)',['M','F','UNKNOWN'])
        #st.write('Patient gender is ', patient_gender)

    with col3:
        patient_age_yrs_group = st.radio('Patient age group:', ['between_18_and_45_years_old',
                                                                    'between_45_and_65_years_old',
                                                                    'over_65_years_old'])
        #st.write('Patient age group is ', patient_age_yrs_group)



    ########################INPUT DATA ARRAY#################
    input_data = (normalized_surgeon_specialty_name,primary_procedure_code,
                  num_proc_codes,hosp_health_ministry,patient_type_group,
                  num_diag_codes,patient_gender,patient_age_yrs_group)
    #with col1:
    #    st.caption(input_data)

    s = [
        {'normalized_surgeon_specialty_name': normalized_surgeon_specialty_name,
         'primary_procedure_code': primary_procedure_code,
         'diagnosis_1': diagnosis_1,
         'num_proc_codes': num_proc_codes,
         'hosp_health_ministry': hosp_health_ministry,
         'patient_type_group': patient_type_group,
         'num_diag_codes': num_diag_codes,
         'patient_gender': patient_gender,
         'patient_age_yrs_group': patient_age_yrs_group,
         },
    ]

    # code for Prediction
    final_message = ''

    # creating a button for Prediction
    with col1:
        if st.button("Surgical time prediction"):
            predicted_value = endpoint.predict(s).predictions[0]['value']
            st.metric(label='Surgical Prediction Time', value=predicted_value)
            st.balloons()


