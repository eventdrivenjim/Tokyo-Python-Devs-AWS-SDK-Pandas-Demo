# BEFORE: Athena query with boto3
import boto3
import time
import pandas as pd
import logging
import os

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
ATHENA_RESULT_LOCATION = os.environ.get('ATHENA_RESULT_LOCATION')

# Initialize Athena client and start query execution
athena = boto3.client("athena")
response = athena.start_query_execution(
    QueryString="SELECT title, genre FROM movies WHERE release_year = 1995",
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
    logger.info(f"Query failed with state: {state}")

print(df.head(10))