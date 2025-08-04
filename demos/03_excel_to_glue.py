# BEFORE and AFTER example using AWS SDK for Pandas

# Configuration - set these environment variables before running
import os
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'company')

# --- BEFORE ---
# BEFORE: Read messy Excel, clean with jaconv, write manually
import pandas as pd
import jaconv
import boto3
import logging

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read Excel file with Japanese text data
df = pd.read_excel("employees.xlsx")

# Standardize Japanese text in title and department columns
# jaconv.z2h() converts full-width characters to half-width (ａ→a, １→1)
# jaconv.hira2kata() converts hiragana to katakana (ひらがな→カタカナ)
df[["title", "department"]] = df[["title", "department"]].applymap(lambda x: jaconv.hira2kata(jaconv.z2h(x)))

# Manually partition data by department and write to S3
# Each department gets its own partition folder
for department, group in df.groupby('department'):
    group.to_parquet(f"s3://{S3_BUCKET_NAME}/employees/department={department}/employees.parquet")

# Manually register partitioned table with Glue Data Catalog
# Define schema, partition keys, and Parquet format specifications
glue = boto3.client("glue")
glue.create_table(
    DatabaseName=GLUE_DATABASE_NAME,
    TableInput={
        "Name": "employees",
        "StorageDescriptor": {
            "Columns": [{"Name": "id", "Type": "string"}, {"Name": "title", "Type": "string"}],
            "Location": f"s3://{S3_BUCKET_NAME}/employees/",
            "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            "SerdeInfo": {"SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"}
        },
        "PartitionKeys": [{"Name": "department", "Type": "string"}]
    }
)

# --- AFTER ---
# AFTER: AWS SDK for Pandas + jaconv to Excel to Glue table
import pandas as pd
import jaconv
import awswrangler as wr
import logging

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read Excel file with Japanese text data
df = pd.read_excel("employees.xlsx")

# Standardize Japanese text in title and department columns
# jaconv.z2h() converts full-width characters to half-width (ａ→a, １→1)
# jaconv.hira2kata() converts hiragana to katakana (ひらがな→カタカナ)
df[["title", "department"]] = df[["title", "department"]].applymap(lambda x: jaconv.hira2kata(jaconv.z2h(x)))

# Write partitioned parquet dataset and auto-register with Glue in one step
# Automatically handles partitioning, S3 upload, and Glue table registration
wr.s3.to_parquet(
    df=df,
    path=f"s3://{S3_BUCKET_NAME}/employees_clean/",
    dataset=True,
    database=GLUE_DATABASE_NAME,
    table="employees",
    partition_cols=["department"]
)