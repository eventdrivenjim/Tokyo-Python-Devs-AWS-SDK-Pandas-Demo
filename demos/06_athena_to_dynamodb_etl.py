# BEFORE and AFTER example using AWS SDK for Pandas
# ETL: Athena analytical queries → DynamoDB for fast operational lookups
# Use case: Transform analytical data into optimized operational lookups

# --- BEFORE ---
# BEFORE: Manual Athena query execution + DynamoDB batch writes
# Requires: Query execution, polling, result retrieval, data transformation, batch writing
import boto3
import pandas as pd
import time
import logging
import os

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - AWS resource identifiers
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
ATHENA_RESULT_LOCATION = os.environ.get('ATHENA_RESULT_LOCATION')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'top-movies')

# Initialize AWS clients - separate clients for each service
athena_client = boto3.client("athena")  # For query execution
dynamodb_resource = boto3.resource("dynamodb")  # For batch writes

# Step 1: Execute analytical query in Athena
# Find movies by popular genres for fast operational lookups
query = """
SELECT 
    movieId,
    title,
    release_year,
    genres,
    CASE 
        WHEN release_year >= 2000 THEN 'Modern'
        ELSE 'Classic'
    END as era
FROM movies 
WHERE contains(genres, 'Action') 
   OR contains(genres, 'Comedy') 
   OR contains(genres, 'Drama')
LIMIT 1000
"""

# Execute query and wait for completion - manual async handling
response = athena_client.start_query_execution(
    QueryString=query,
    QueryExecutionContext={"Database": GLUE_DATABASE_NAME},
    ResultConfiguration={"OutputLocation": ATHENA_RESULT_LOCATION}
)

query_id = response["QueryExecutionId"]

# Poll for completion - manual status checking with sleep intervals
while True:
    execution_details = athena_client.get_query_execution(QueryExecutionId=query_id)
    state = execution_details["QueryExecution"]["Status"]["State"]
    if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
        break
    time.sleep(2)  # Wait 2 seconds between status checks

if state != "SUCCEEDED":
    raise Exception(f"Query failed with state: {state}")

# Load results from S3 - manual CSV retrieval
# Athena stores results as CSV files in S3
result_df = pd.read_csv(f"{ATHENA_RESULT_LOCATION.rstrip('/')}/{query_id}.csv")

# Write to DynamoDB with manual batch operations
# Requires manual type conversion and batch management
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)

try:
    with table.batch_writer() as batch:  # Handles batching automatically
        for _, row in result_df.iterrows():
            # Convert to DynamoDB item format - manual type conversion required
            item = {
                'pk': row['pk'],  # Partition key for query efficiency
                'sk': row['movie_key'],  # Sort key for range queries
                'title': row['title'],
                'release_year': int(row['release_year']),  # Must convert to int
                'genres': row['genres'],
                'era': row['era']
            }
            batch.put_item(Item=item)
    
    logger.info(f"Successfully loaded {len(result_df)} movies to DynamoDB")
    
except Exception as e:
    logger.error(f"Error writing to DynamoDB: {e}")

# --- AFTER ---
# AFTER: Streamlined ETL with awswrangler
# Simplifies: Query execution, result handling, and DynamoDB writes
import awswrangler as wr
import logging
import os

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - same resources, simpler usage
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'top-movies')

# Step 1: Execute analytical query and get results directly
# Same SQL query as BEFORE section (with comma fix)
query = """
SELECT 
    movieId,
    title,
    release_year,
    genres,
    CASE 
        WHEN release_year >= 2000 THEN 'Modern'
        ELSE 'Classic'
    END as era
FROM movies 
WHERE contains(genres, 'Action') 
   OR contains(genres, 'Comedy') 
   OR contains(genres, 'Drama')
LIMIT 1000
"""

# Single function call handles query execution, polling, and result retrieval
# Automatically manages: async execution, status polling, S3 result retrieval
result_df = wr.athena.read_sql_query(
    sql=query,
    database=GLUE_DATABASE_NAME
)

# Step 2: Write to DynamoDB in one operation
# Automatically handles: batching, retries, type conversions, error handling
wr.dynamodb.put_df(
    df=result_df,
    table_name=DYNAMODB_TABLE_NAME
)

logger.info(f"ETL completed: {len(result_df)} movies transferred from Athena to DynamoDB")