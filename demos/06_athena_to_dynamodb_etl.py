# BEFORE and AFTER example using AWS SDK for Pandas
# ETL: Athena analytical queries → DynamoDB for fast operational lookups

# Configuration - set these environment variables before running
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
ATHENA_RESULT_LOCATION = os.environ.get('ATHENA_RESULT_LOCATION')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'top-movies')

# --- BEFORE ---
# BEFORE: Manual Athena query execution + DynamoDB batch writes
import boto3
import pandas as pd
import time
import logging

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
athena_client = boto3.client("athena")
dynamodb_resource = boto3.resource("dynamodb")

# Step 1: Execute analytical query in Athena
# Find top-rated movies by genre for fast operational lookups
query = """
SELECT 
    title,
    release_year,
    genres,
    is_remake,
    CASE 
        WHEN release_year >= 2000 THEN 'Modern'
        ELSE 'Classic'
    END as era
FROM movies 
WHERE contains(genres, 'Action') 
   OR contains(genres, 'Comedy') 
   OR contains(genres, 'Drama')
ORDER BY release_year DESC
LIMIT 500
"""

# Execute query and wait for completion
response = athena_client.start_query_execution(
    QueryString=query,
    QueryExecutionContext={"Database": GLUE_DATABASE_NAME},
    ResultConfiguration={"OutputLocation": ATHENA_RESULT_LOCATION}
)

query_id = response["QueryExecutionId"]

# Poll for completion
while True:
    execution_details = athena_client.get_query_execution(QueryExecutionId=query_id)
    state = execution_details["QueryExecution"]["Status"]["State"]
    if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
        break
    time.sleep(2)

if state != "SUCCEEDED":
    raise Exception(f"Query failed with state: {state}")

# Step 2: Load results from S3
result_df = pd.read_csv(f"{ATHENA_RESULT_LOCATION.rstrip('/')}/{query_id}.csv")

# Step 3: Transform for DynamoDB optimization
# Add partition key for efficient queries
result_df['pk'] = result_df['genres'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown')
result_df['movie_key'] = result_df['title'] + '#' + result_df['release_year'].astype(str)

# Step 4: Write to DynamoDB with manual batch operations
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)

try:
    with table.batch_writer() as batch:
        for _, row in result_df.iterrows():
            # Convert to DynamoDB item format
            item = {
                'pk': row['pk'],
                'sk': row['movie_key'],
                'title': row['title'],
                'release_year': int(row['release_year']),
                'genres': row['genres'],
                'is_remake': bool(row['is_remake']),
                'era': row['era']
            }
            batch.put_item(Item=item)
    
    logger.info(f"Successfully loaded {len(result_df)} movies to DynamoDB")
    
except Exception as e:
    logger.error(f"Error writing to DynamoDB: {e}")

# --- AFTER ---
# AFTER: Streamlined ETL with awswrangler
import awswrangler as wr
import logging

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Step 1: Execute analytical query and get results directly
query = """
SELECT 
    title,
    release_year,
    genres,
    is_remake,
    CASE 
        WHEN release_year >= 2000 THEN 'Modern'
        ELSE 'Classic'
    END as era
FROM movies 
WHERE contains(genres, 'Action') 
   OR contains(genres, 'Comedy') 
   OR contains(genres, 'Drama')
ORDER BY release_year DESC
LIMIT 500
"""

# Single function call handles query execution, polling, and result retrieval
result_df = wr.athena.read_sql_query(
    sql=query,
    database=GLUE_DATABASE_NAME
)

# Step 2: Transform for DynamoDB optimization
# Add partition key for efficient queries
result_df['pk'] = result_df['genres'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown')
result_df['movie_key'] = result_df['title'] + '#' + result_df['release_year'].astype(str)

# Step 3: Write to DynamoDB in one operation
# Automatically handles batching, retries, and type conversions
wr.dynamodb.put_df(
    df=result_df,
    table_name=DYNAMODB_TABLE_NAME
)

logger.info(f"ETL completed: {len(result_df)} movies transferred from Athena to DynamoDB")