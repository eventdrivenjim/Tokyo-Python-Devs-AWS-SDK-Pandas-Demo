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

