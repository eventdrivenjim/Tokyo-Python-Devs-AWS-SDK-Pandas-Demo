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