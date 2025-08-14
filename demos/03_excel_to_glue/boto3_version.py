# BEFORE: Read messy Excel, clean with jaconv, write manually
import pandas as pd
import jaconv
import boto3
import logging
import os

# Configure logging for BEFORE section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')

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
    DatabaseName="employees",
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
