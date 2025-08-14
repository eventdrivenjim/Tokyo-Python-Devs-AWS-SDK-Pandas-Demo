# BEFORE: Batch get movies from DynamoDB with boto3
import boto3
import pandas as pd
import logging

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# env variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'demo-table-name-changeme')

# Initialize DynamoDB client
dynamodb = boto3.client("dynamodb")

# Define specific movie IDs to lookup
movie_ids = ["1", "2", "3", "10", "32"]

# Format keys with DynamoDB type annotations
# DynamoDB requires explicit type specification: {'S': string, 'N': number, etc.}
keys = [{"movieid": {"S": movie_id}} for movie_id in movie_ids]

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
    logger.info(f"Warning: {len(response['UnprocessedKeys'])} items were not processed")

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

