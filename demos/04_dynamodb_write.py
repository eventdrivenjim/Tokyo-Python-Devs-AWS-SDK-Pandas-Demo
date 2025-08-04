# BEFORE and AFTER example using AWS SDK for Pandas

# Configuration - set these environment variables before running
import os
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'movies')

# --- BEFORE ---
# BEFORE: Read CSV and write to DynamoDB with boto3
import pandas as pd
import boto3

# Initialize DynamoDB resource and table
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Read movies CSV from S3 and limit to first 1000 rows
df = pd.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv").head(1000)

# Extract year and clean title
df['year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)


# Write to DynamoDB using batch operations with error handling
# DynamoDB batch_write_item has a 25-item limit per request
# batch_writer() automatically handles:
# - Chunking 1000 items into ~40 batch requests (1000 ÷ 25)
# - Retrying unprocessed items automatically
# - Rate limiting and exponential backoff
try:
    with table.batch_writer() as batch:
        for _, row in df.iterrows():
            item = row.to_dict()
            batch.put_item(Item=item)
except Exception as e:
    print(f"Error writing to DynamoDB: {e}")

# --- AFTER ---
# AFTER: Read CSV and write to DynamoDB with awswrangler
import awswrangler as wr

# Read movies CSV from S3 and limit to first 1000 rows
df = wr.s3.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv").head(1000)

# Extract year and clean title
df['year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)

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