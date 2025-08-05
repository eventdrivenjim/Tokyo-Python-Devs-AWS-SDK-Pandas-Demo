# AFTER: AWS SDK for Pandas + jaconv to Excel to Glue table
import pandas as pd
import jaconv
import awswrangler as wr
import logging
import os

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'demo-bucket-changeme')
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'company')

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

print(df.head(10))