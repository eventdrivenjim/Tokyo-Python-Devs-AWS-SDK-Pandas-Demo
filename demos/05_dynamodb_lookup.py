# BEFORE and AFTER example using AWS SDK for Pandas

# Configuration - set these environment variables before running
import os
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'movies')

# --- BEFORE ---
# BEFORE: Batch get movies from DynamoDB with boto3
import boto3
import pandas as pd

# Initialize DynamoDB client
dynamodb = boto3.client("dynamodb")

# Define specific movie IDs to lookup
movie_ids = ["1", "2", "3", "10", "32"]

# Format keys with DynamoDB type annotations
# DynamoDB requires explicit type specification: {'S': string, 'N': number, etc.}
keys = [{"movieid": {"S": mid}} for mid in movie_ids]

# Perform batch get operation with multiple parameters
# batch_get_item limitations:
# - Maximum 100 items per request
# - Must specify table name in RequestItems
# - Keys must include DynamoDB type annotations
# - ProjectionExpression limits returned attributes
response = dynamodb.batch_get_item(
    RequestItems={
        DYNAMODB_TABLE_NAME: {
            "Keys": keys,
            "ProjectionExpression": "movieid, title, genres",
            "ConsistentRead": False  # Eventually consistent by default
        }
    }
)

# Handle potential unprocessed keys (if throttling occurs)
if 'UnprocessedKeys' in response and response['UnprocessedKeys']:
    print(f"Warning: {len(response['UnprocessedKeys'])} items were not processed")

# Extract items from nested response structure
items = response["Responses"][DYNAMODB_TABLE_NAME]
results = []

# Manually convert each item from DynamoDB format to regular Python dict
for item in items:
    # DynamoDB returns data with type descriptors: {'S': 'value', 'N': '123'}
    # Must manually extract the actual values from type wrappers
    movie = {
        'movieid': item['movieid']['S'],  # String type
        'title': item['title']['S'],      # String type
        'genres': item['genres']['S']     # String type
    }
    results.append(movie)

# Manually create DataFrame from processed results
df = pd.DataFrame(results)

# Export DataFrame to parquet file on S3
df.to_parquet(f"s3://{S3_BUCKET_NAME}/movie_lookup_results.parquet")

# --- AFTER ---
# AFTER: Get DynamoDB movies as DataFrame using awswrangler
import awswrangler as wr

# Define same movie IDs to lookup
movie_ids = ["1", "2", "3", "10", "32"]

# Create keys in simple format - no DynamoDB type annotations needed
keys = [{"movieid": mid} for mid in movie_ids]

# Single function call handles all complexity automatically:
# - DynamoDB type annotations
# - Batch request management (100-item limit)
# - Unprocessed key handling and retries
# - Type conversion from DynamoDB format
# - DataFrame creation and optimization
df = wr.dynamodb.get_items(
    table_name=DYNAMODB_TABLE_NAME,
    keys=keys
)

# Export DataFrame to parquet file on S3
wr.s3.to_parquet(
    df=df,
    path=f"s3://{S3_BUCKET_NAME}/movie_lookup_results.parquet"
)