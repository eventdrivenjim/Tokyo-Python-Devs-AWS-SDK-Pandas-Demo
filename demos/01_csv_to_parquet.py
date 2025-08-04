# BEFORE and AFTER example using AWS SDK for Pandas

# --- BEFORE ---
# BEFORE: Pandas + boto3 to write Parquet and register with Glue
import pandas as pd
import boto3
import logging
from datetime import datetime 
import os

# ENVIRONMENT VARIABLES
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'demo-glue-catalog-changeme')

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client("s3")
glue = boto3.client("glue")

# Read CSV from S3
df = pd.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv")

# Extract clean title and year, detect remakes
df[['title', 'release_year']] = df['title'].str.extract(r'^(.*?)\s*\((\d{4})\)')

# Handle invalid years gracefully - best practice for production code
df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
initial_count = len(df)
df = df.dropna(subset=['release_year'])  # Remove rows with invalid years
dropped_count = initial_count - len(df)
if dropped_count > 0:
    logger.warning(f"Dropped {dropped_count} rows with invalid years")
df['release_year'] = df['release_year'].astype(int)

# Get current year for dynamic categorization
current_year = datetime.now().year

# Categorize by film era (>25 years = Classic)
df['age_category'] = pd.cut(df['release_year'], 
    bins=[1900, current_year-25, current_year+1], 
    labels=['Classic', 'Modern'])

# Mark remakes - True for later versions of same title, False for original
# Unfortunately hollywood makes this too often
df['is_remake'] = df.groupby('title')['release_year'].transform(lambda x: x != x.min())

# Convert pipe-separated genres to list for better searchability
# Athena can query arrays with contains() function: WHERE contains(genres, 'Action')
# Note: contains() is case-sensitive - MovieLens uses proper case (Action, Comedy, Sci-Fi)
df['genres'] = df['genres'].str.split('|')

# Manually partition data by release_year and upload to S3
for release_year, group in df.groupby('release_year'):
    # Save each year's data to local parquet file
    parquet_file = f"/tmp/movies_year_{release_year}.parquet"
    group.to_parquet(parquet_file)
    # Upload to S3 with partition structure
    with open(parquet_file, "rb") as f:
        s3.upload_fileobj(f, S3_BUCKET_NAME, f"movies/release_year={release_year}/movies.parquet")

# Manually register partitioned table with Glue Data Catalog
glue.create_table(
    DatabaseName=GLUE_DATABASE_NAME,
    TableInput={
        "Name": "movies",
        "StorageDescriptor": {
            # Define schema for all columns except partition column
            "Columns": [{"Name": col, "Type": "string"} for col in df.columns if col != "release_year"],
            "Location": f"s3://{S3_BUCKET_NAME}/movies/",
            # Specify Parquet input/output formats
            "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            "SerdeInfo": {"SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"}
        },
        # Define partition column
        "PartitionKeys": [{"Name": "release_year", "Type": "int"}]
    }
)

# --- AFTER ---
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

# Extract clean title and release year, detect remakes
df[['title', 'release_year']] = df['title'].str.extract(r'^(.*?)\s*\((\d{4})\)')

# Handle invalid years gracefully - best practice for production code
df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
initial_count = len(df)
df = df.dropna(subset=['release_year'])  # Remove rows with invalid years
dropped_count = initial_count - len(df)
if dropped_count > 0:
    logger.warning(f"Dropped {dropped_count} rows with invalid years")
df['release_year'] = df['release_year'].astype(int)

# Validate year range - removes movies outside 1900-2030 range
# This filters out pre-1900 films, future dates, and data entry errors
invalid_years = ~df['release_year'].between(1900, 2030)
if invalid_years.any():
    invalid_count = invalid_years.sum()
    logger.warning(f"Found {invalid_count} movies with invalid years, filtering them out")
    logger.warning(f"Invalid years: {df.loc[invalid_years, 'release_year'].unique()}")
    df = df[~invalid_years]  # Keep only movies with years 1900-2030
else:
    logger.info("All release years are valid (1900-2030)")

# Get current year for dynamic categorization
current_year = datetime.now().year

# Categorize by film era (>25 years = Classic)
df['age_category'] = pd.cut(df['release_year'], 
    bins=[1900, current_year-25, current_year+1], 
    labels=['Classic', 'Modern'])

# Mark remakes - True for later versions of same title, False for original
df['is_remake'] = df.groupby('title')['release_year'].transform(lambda x: x != x.min())

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