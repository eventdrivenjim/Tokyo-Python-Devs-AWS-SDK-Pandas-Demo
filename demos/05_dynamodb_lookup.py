# BEFORE and AFTER example using AWS SDK for Pandas


# --- BEFORE ---
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

# --- AFTER ---
# AFTER: Get DynamoDB movies as DataFrame using awswrangler
import awswrangler as wr
from datetime import datetime
import logging

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# env variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'table-name-changeme')

# Define same movie IDs to lookup
movie_ids = ["1", "2", "3", "10", "32"]

# Create keys in simple format - no DynamoDB type annotations needed
keys = [{"movieid": movie_id} for movie_id in movie_ids]

# Single function call handles all complexity automatically:
# - DynamoDB type annotations
# - Batch request management (100-item limit)
# - Unprocessed key handling and retries
# - Type conversion from DynamoDB format
# - DataFrame creation and optimization
# Note: DynamoDB excels at key-based lookups like this, but would be inefficient for genre searches (requires expensive table scan). 
# Use Athena/Redshift Spectrum for analytical queries.
df = wr.dynamodb.get_items(
    table_name=DYNAMODB_TABLE_NAME,
    keys=keys
)

# Fun data analysis: Calculate movie age and genre diversity
current_year = datetime.now().year
df['movie_age'] = current_year - df['year'].astype(int)
df['genre_count'] = df['genres'].apply(len)
df['age_category'] = df['movie_age'].apply(lambda x: 'Classic' if x > 25 else 'Modern')

# Display insights
logger.info(f"Average movie age: {df['movie_age'].mean():.1f} years")
logger.info(f"Average genres per movie: {df['genre_count'].mean():.1f}")
logger.info(f"Classic movies (25+ years): {(df['age_category'] == 'Classic').sum()}/{len(df)}")

# Export DataFrame to parquet file on S3
wr.s3.to_parquet(
    df=df,
    path=f"s3://{S3_BUCKET_NAME}/movie_lookup_results.parquet"
)