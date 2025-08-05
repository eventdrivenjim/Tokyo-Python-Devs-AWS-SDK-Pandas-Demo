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