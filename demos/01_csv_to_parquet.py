# BEFORE and AFTER example using AWS SDK for Pandas

# Configuration - set these environment variables before running
import os
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')

# --- BEFORE ---
# BEFORE: Pandas + boto3 to write Parquet and register with Glue
import pandas as pd
import boto3

# Initialize AWS clients
s3 = boto3.client("s3")
glue = boto3.client("glue")

# Read CSV from S3
df = pd.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv")

# Extract year and clean title for partitioning
df['year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)

# Manually partition data by year and upload to S3
for year, group in df.groupby('year'):
    # Save each year's data to local parquet file
    parquet_file = f"/tmp/movies_year_{year}.parquet"
    group.to_parquet(parquet_file)
    # Upload to S3 with partition structure
    with open(parquet_file, "rb") as f:
        s3.upload_fileobj(f, S3_BUCKET_NAME, f"movies/year={year}/movies.parquet")

# Manually register partitioned table with Glue Data Catalog
glue.create_table(
    DatabaseName=GLUE_DATABASE_NAME,
    TableInput={
        "Name": "movies",
        "StorageDescriptor": {
            # Define schema for all columns except partition column
            "Columns": [{"Name": col, "Type": "string"} for col in df.columns if col != "year"],
            "Location": f"s3://{S3_BUCKET_NAME}/movies/",
            # Specify Parquet input/output formats
            "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            "SerdeInfo": {"SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"}
        },
        # Define partition column
        "PartitionKeys": [{"Name": "year", "Type": "string"}]
    }
)

# --- AFTER ---
# AFTER: AWS SDK for Pandas (wrangler) simplifies the entire flow
import awswrangler as wr

# Read CSV from S3
df = wr.s3.read_csv(f"s3://{S3_BUCKET_NAME}/movies.csv")

# Extract year and clean title for partitioning
df['year'] = df['title'].str.extract(r'\((\d{4})\)')
df['title'] = df['title'].str.replace(r'\s*\(\d{4}\).*$', '', regex=True)

# Write partitioned parquet dataset and auto-register with Glue in one step
# This single function call handles partitioning by year, uploading to S3,
# and registering the table schema with Glue Data Catalog automatically
wr.s3.to_parquet(
    df=df,
    path=f"s3://{S3_BUCKET_NAME}/movies_parquet/",
    dataset=True,
    database=GLUE_DATABASE_NAME,
    table="movies",
    partition_cols=["year"]
)