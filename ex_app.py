#!pip install ipython-autotime
# %load_ext autotime
import os
from tabulate import tabulate
import numpy as np
from google.cloud import aiplatform as aip
from google.cloud import bigquery
import pandas as pd
import streamlit as st

import plotly
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import time
import plotly.graph_objects as go

####################
NOTEBOOK = 'Vertex_AI_Streamlit'
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
GCS_BUCKET = f"gs://{BUCKET}"
######################
aip.init(
    project=PROJECT,
    location=REGION,
    staging_bucket=GCS_BUCKET)

ENDPOINT_NAME = 'projects/69318036822/locations/us-central1/endpoints/4074389870305345536'
#ENDPOINT_NAME = 'projects/69318036822/locations/us-central1/endpoints/4718085758647271424'

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

st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)

# *************SIDEBAR*************#
with st.sidebar:
    st.title('Baby Weight Prediction')
    # Input:
    is_male = st.radio('What is the gender of the baby?', ['Boy', 'Girl'])
    mother_age = st.slider('What is the age of the mother?', 10, 100, 20)
    gestation_weeks = st.slider('The number of weeks of the pregnancy:', 10, 50, 39)
    cigarette_use = st.radio('Maternal smoking status:', ['Unknown','Yes', 'No'])
    alcohol_use = st.radio('Maternal drinking status:', ['Unknown','Yes', 'No'])
    plurality = st.selectbox('How many children were born as a result of this pregnancy?',
                             ['single(1)', 'Twins(2)', 'Triplets(3)', 'Quadruplets(4)'])

# *************GENERATE INPUT*************#

if is_male == 'Boy':
    is_male = 'true'
else:
    is_male = 'false'

if cigarette_use == 'Yes':
    cigarette_use = 'true'
elif cigarette_use == 'Unknown':
    cigarette_use = 'Unknown'
else:
    cigarette_use = 'false'

if alcohol_use == 'Yes':
    alcohol_use = 'true'
elif alcohol_use == 'Unknown':
    alcohol_use = 'Unknown'
else:
    alcohol_use = 'false'

instance = [
    {'is_male': is_male,
     'mother_age': str(mother_age),
     'plurality': plurality,
     'gestation_weeks': str(gestation_weeks),
     'cigarette_use': cigarette_use,
     'alcohol_use': alcohol_use,
     },
]

# st.write(instance)
# *************GENERATE RESULT*************#
predicted_value = ''

# *************EXPLAINATION RESULT*************#
explain = endpoint.explain(instance)

FEATURE_COLUMNS = [
    'is_male',
    'mother_age',
    'plurality',
    'gestation_weeks',
    'cigarette_use',
    'alcohol_use'
]


# ************************FUNCTION**********************
def get_feature_attributions(
        prediction_expl, instance_index, feature_columns=FEATURE_COLUMNS):
    """Returns the feature attributions with the baseline for a prediction example"""

    rows = []
    attribution = prediction_expl.explanations[instance_index].attributions[0]
    baseline_score = attribution.baseline_output_value
    total_att_val = baseline_score
    for key in feature_columns:
        feature_val = instance[instance_index][key]
        att_val = attribution.feature_attributions[key]
        total_att_val += att_val
        rows.append([key, feature_val, att_val])

    feature_attributions_rows = sorted(rows, key=lambda row: row[2], reverse=True)
    feature_attributions_rows.insert(0, ["Baseline_Score", "--", baseline_score])
    feature_attributions_rows.append(["Final_Prediction", "--", total_att_val])

    return feature_attributions_rows

feature_attributions_rows = get_feature_attributions(explain, 0)

def generate_dataframe():
    feature_list = []
    feature_values = []
    feature_contributions = []
    feature_attributions_rows = get_feature_attributions(explain, 0)

    for i in range(len(feature_attributions_rows)):
        feature = feature_attributions_rows[i][0]
        feature_list.append(feature)

    for i in range(len(feature_attributions_rows)):
        feature = feature_attributions_rows[i][1]
        feature_values.append(feature)

    for i in range(len(feature_attributions_rows)):
        feature = feature_attributions_rows[i][2]
        feature_contributions.append(feature)

    zipped = list(zip(feature_list, feature_values, feature_contributions))
    df = pd.DataFrame(zipped, columns=['Feature', 'Value', 'Contribution'])

    return df, feature_list, feature_values, feature_contributions

df, feature_list, feature_values, feature_contributions = generate_dataframe()

###############

if is_male == 'true':
    is_male = 'Boy'
else:
    is_male = 'Girl'

if cigarette_use == 'true':
    cigarette_use = 'Smoking'
elif cigarette_use == 'Unknown':
    cigarette_use = 'Unknown'
else:
    cigarette_use = 'No Smoking'

if alcohol_use == 'true':
    alcohol_use = 'Drinking'
elif alcohol_use == 'Unknown':
    alcohol_use = 'Unknown'
else:
    alcohol_use = 'No Drinking'
# st.write(instance)
# copy df
df3 = df.copy()
df3 = df3.set_index('Feature')
# st.dataframe(df)
# st.dataframe(df3)

#####################USER INPUT DISPLAY######################

col1, col2, col3, col4, col5 = st.columns(5)
st.columns([1, 1, 3, 1, 1])

col1.metric("Baby Gender", is_male.upper(), df3.loc['is_male', 'Contribution'])
col1.metric("Mother Age", mother_age, df3.loc['mother_age', 'Contribution'])
col2.metric("Plurality", plurality.upper(), df3.loc['plurality', 'Contribution'])
col2.metric("Gestation Week Number", gestation_weeks, df3.loc['gestation_weeks', 'Contribution'])
col3.metric("Maternal smoking status", cigarette_use.upper(), df3.loc['cigarette_use', 'Contribution'])
col3.metric("Maternal drinking status", alcohol_use.upper(), df3.loc['alcohol_use', 'Contribution'])

# Display the Prediction in LBs
predicted_value = round(endpoint.predict(instance).predictions[0]['value'], 2)
with st.spinner('Generating Result...'):
    time.sleep(1)

with col5:
    st.subheader("Baby Weight Prediction:")
    st.title(f"{predicted_value} LB")

# water fall horizontall


# layout
df["Color"] = np.where(df["Contribution"] < 0, 'Negative Contribution', 'Positive Contribution')
fig = go.Figure(go.Waterfall(
    orientation="h",
    measure=["relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"],
    y=feature_list,
    x=feature_contributions,
    text=feature_contributions,textposition='outside',
    connector={"mode": "between", "line": {"width": 4, "color": "rgb(0, 0, 0)", "dash": "solid"}}
))
#st.subheader('Feature Importance')
st.plotly_chart(fig, use_container_width=True)
#########
df5 = df.query("Feature not in ('Baseline_Score','Final_Prediction')")
fig = px.bar(df5, x='Contribution', y='Feature',
             color='Color', category_orders=df['Feature'],
             text_auto=True)
st.plotly_chart(fig, use_container_width=True)

df5 = df.query("Feature not in ('Baseline_Score','Final_Prediction')")

df6 = df5[['Feature','Contribution']]
st.table(df6)




