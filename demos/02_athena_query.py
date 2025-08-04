# BEFORE and AFTER example using AWS SDK for Pandas

# Configuration - set these environment variables before running
import os
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
ATHENA_RESULT_LOCATION = os.environ.get('ATHENA_RESULT_LOCATION')

# --- BEFORE ---
# BEFORE: Athena query with boto3
import boto3
import time
import pandas as pd

# Initialize Athena client and start query execution
athena = boto3.client("athena")
response = athena.start_query_execution(
    QueryString="SELECT title, genre FROM movies WHERE year = 1995",
    QueryExecutionContext={"Database": GLUE_DATABASE_NAME},
    ResultConfiguration={"OutputLocation": ATHENA_RESULT_LOCATION}
)

# Poll for query completion status manually
# Must continuously check until query finishes (succeeded, failed, or cancelled)
query_id = response["QueryExecutionId"]
while True:
    execution_details = athena.get_query_execution(QueryExecutionId=query_id)
    state = execution_details["QueryExecution"]["Status"]["State"]
    if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
        break
    time.sleep(1)

# Load results from S3 after query completes
if state == "SUCCEEDED":
    df = pd.read_csv(f"{ATHENA_RESULT_LOCATION.rstrip('/')}/{query_id}.csv")
else:
    print(f"Query failed with state: {state}")

# --- AFTER ---
# AFTER: Query Athena with awswrangler
import awswrangler as wr

# Execute query and return results as dataframe in one step
# Automatically handles query execution, polling, and result loading
df = wr.athena.read_sql_query(
    sql="SELECT title, genre FROM movies WHERE year = 1995",
    database=GLUE_DATABASE_NAME
)