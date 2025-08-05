# AFTER: AWS SDK for Pandas (wrangler) simplifies the entire flow
import awswrangler as wr
import logging
from datetime import datetime

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENVIRONMENT VARIABLES
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'demo-glue-catalog-changeme')

# Read CSV from S3
df = wr.s3.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv")

# Extract clean title and release year
df[['title', 'release_year']] = df['title'].str.extract(r'^(.*?)\s*\((\d{4})\)')

# Handle invalid years gracefully - best practice for production code
df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')

# Convert pipe-separated genres to list for better searchability
# Athena can query arrays with contains() function: WHERE contains(genres, 'Action')
# Note: contains() is case-sensitive - MovieLens uses proper case (Action, Comedy, Sci-Fi)
df['genres'] = df['genres'].str.split('|')

# Write partitioned parquet dataset and auto-register with Glue in one step
# This single function call handles partitioning by year, uploading to S3,
# and registering the table schema with Glue Data Catalog automatically
# Store release year as integer, not string
wr.s3.to_parquet(
    df=df,
    path=f"s3://{S3_BUCKET_NAME}/movies/",
    dataset=True,
    database=GLUE_DATABASE_NAME,
    table="movies",
    partition_cols=["release_year"],
    dtype={'release_year': 'int64'}  

)