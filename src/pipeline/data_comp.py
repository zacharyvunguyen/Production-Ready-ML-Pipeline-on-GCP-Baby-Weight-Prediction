# Components
import sys
import os
from kfp.v2.dsl import component
from typing import NamedTuple


#######################################################################
# component that ingests a portion of data from the BQ table
# that will be used for modeling, including the several steps:
# preprocesses data,
# adds the slits column, 
# export data into a new BQ table,
@component(
    base_image="python:3.9",
    packages_to_install=[ "bigquery",]
)
def extract_source_data(
    project: str,
    region:str,
    year: int,
    in_bq_table_id: str, 
    out_bq_table_id: str,
) -> NamedTuple(
    "Outputs", [("out_bq_table_uri", str)]
):
    
    from google.cloud import bigquery
    from collections import namedtuple
    
    bqclient = bigquery.Client(project=project)
    query = f"""
    CREATE OR REPLACE TABLE `{out_bq_table_id}` AS (
    SELECT
        weight_pounds,
        is_male,
        mother_age,
        plurality,
        gestation_weeks,
        cigarette_use,
        alcohol_use,
        year, month, wday, state, mother_birth_state    
    FROM
        {in_bq_table_id}
    WHERE
        year > {year} 
        AND weight_pounds > 0
        AND mother_age > 0
        AND plurality > 0
        AND gestation_weeks > 19     
    )
    """
   
    response = bqclient.query(query)
    _ = response.result()   
    
    # return output parameters
    out_bq_table_uri = f"bq://{out_bq_table_id}"
    outputs = namedtuple("Outputs", ["out_bq_table_uri"])
    
    return outputs(out_bq_table_uri)

#######################################################################
# component that ingests a portion of data from the BQ table
# that will be used for modeling, including the several steps:
# preprocesses data,
# adds the slits column, 
# export data into a new BQ table,
@component(
    base_image="python:3.9",
    packages_to_install=[ "bigquery",]
)
def preprocess_data(
    project: str,
    region:str,
    limit:int,
    in_bq_table_id: str, 
    out_bq_table_id: str,
) -> NamedTuple(
    "Outputs", [("out_bq_table_uri", str)]
):
    
    from google.cloud import bigquery
    from collections import namedtuple
    
    bqclient = bigquery.Client(project=project)
    query = f"""
    CREATE OR REPLACE TABLE `{out_bq_table_id}` AS (
        WITH all_hash_limit AS (
            SELECT
                weight_pounds,
                CAST(is_male AS STRING) AS is_male,
                mother_age,
                CASE
                    WHEN plurality = 1 THEN "Single(1)"
                    WHEN plurality = 2 THEN "Twins(2)"
                    WHEN plurality = 3 THEN "Triplets(3)"
                    WHEN plurality = 4 THEN "Quadruplets(4)"
                    WHEN plurality = 5 THEN "Quintuplets(5)"
                END AS plurality,
                gestation_weeks,
                IFNULL(CAST(cigarette_use AS STRING), "Unknown") AS cigarette_use,
                IFNULL(CAST(alcohol_use AS STRING), "Unknown") AS alcohol_use,
                ABS(FARM_FINGERPRINT(
                    CONCAT(
                        CAST(year AS STRING),
                        CAST(month AS STRING),
                        CAST(COALESCE(wday, 0)  AS STRING),
                        CAST(IFNULL(state, "Unknown") AS STRING),
                        CAST(IFNULL(mother_birth_state, "Unknown")  AS STRING)
                    )
                )) AS hash_values
            FROM
                `{in_bq_table_id}`
            LIMIT {limit}
        )
        SELECT * EXCEPT(hash_values),
            CASE 
                WHEN MOD(hash_values,10) < 8 THEN "TRAIN" 
                WHEN MOD(hash_values,10) < 9 THEN "VALIDATE"
                ELSE "TEST"
            END AS splits
        FROM all_hash_limit
    )
    """
   
    response = bqclient.query(query)
    _ = response.result()   
    
    # return output parameters
    out_bq_table_uri = f"bq://{out_bq_table_id}"
    outputs = namedtuple("Outputs", ["out_bq_table_uri"])
    
    return outputs(out_bq_table_uri)