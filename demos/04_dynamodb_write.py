# BEFORE and AFTER example using AWS SDK for Pandas

# --- BEFORE ---
# BEFORE: Manual individual DynamoDB writes with complex type conversion
import pandas as pd
import boto3
import time
import logging
import os
from botocore.exceptions import ClientError

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'movies')

# Initialize DynamoDB client (not resource) for manual type handling
dynamodb = boto3.client("dynamodb")

# Read movies CSV from S3 and limit to first 100 rows for demo
df = pd.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv").head(100)

# Extract year and clean title
df['release_year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)

# Convert pipe-separated genres to list for better searchability
df['genres'] = df['genres'].str.split('|')

# Manual individual writes with type conversion and error handling
successful_writes = 0
failed_writes = 0

for _, row in df.iterrows():
    try:
        # Manual DynamoDB type conversion - required for each field
        # DynamoDB requires explicit type annotations: S=String, N=Number, SS=StringSet
        item = {
            'movieId': {'S': str(row['movieId'])},           # String type
            'title': {'S': str(row['title'])},               # String type  
            'release_year': {'N': str(row['release_year'])}, # Number type (as string)
            'genres': {'SS': row['genres']}                  # String Set type
        }
        
        # Individual put_item call - no batching optimization
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item=item
        )
        successful_writes += 1
        
        # Rate limiting to avoid throttling - manual delay between writes
        time.sleep(0.01)  # 10ms delay between writes
        
    except ClientError as e:
        failed_writes += 1
        if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
            time.sleep(1)  # Back off on throttling
        logger.error(f"Failed to write item {row['movieId']}: {e}")
    except Exception as e:
        failed_writes += 1
        logger.error(f"Unexpected error for item {row['movieId']}: {e}")

logger.info(f"Completed: {successful_writes} successful, {failed_writes} failed")

# --- AFTER ---
# AFTER: Read CSV and write to DynamoDB with awswrangler
import awswrangler as wr
import logging

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'movies')

# Read movies CSV from S3 and limit to first 1000 rows
df = wr.s3.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv").head(1000)

# Extract year and clean title
df['release_year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)

# Convert pipe-separated genres to list for better searchability
df['genres'] = df['genres'].str.split('|')

# Write entire dataframe to DynamoDB in one operation
# Automatically handles all the complexity:
# - Batching into 25-item chunks
# - Error handling and retries
# - Data type conversions
# - Rate limiting
wr.dynamodb.put_df(
    df=df,
    table_name=DYNAMODB_TABLE_NAME
)