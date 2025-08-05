# Demo 01: CSV to Parquet Conversion with Glue Registration

## Overview
Demonstrates converting CSV files to partitioned Parquet format and registering the table schema with AWS Glue Data Catalog.

## Use Case
Transform raw CSV data into optimized Parquet format for better query performance and automatic schema registration for analytics.

## Files
- `boto3.py` - **BEFORE**: Manual partitioning, S3 uploads, and Glue schema registration
- `wrangler.py` - **AFTER**: Single function call handles everything

## Key Differences

### BEFORE (boto3.py)
- Manual data partitioning by release year
- Individual S3 uploads for each partition
- Complex Glue table schema definition
- Manual column type specification
- ~40 lines of code

### AFTER (wrangler.py)
- Automatic partitioning and S3 upload
- Automatic Glue table registration
- Automatic schema inference
- 1 function call: `wr.s3.to_parquet()`
- ~3 lines of core logic

## Benefits Demonstrated
- **80% code reduction**: From 40+ lines to 3 lines
- **Automatic optimization**: Handles partitioning strategy
- **Schema management**: Automatic Glue catalog registration
- **Error handling**: Built-in retry and error management

## Prerequisites
- S3 bucket configured
- Glue database created
- MovieLens movies.csv uploaded to S3

## Usage
```bash
# Run BEFORE example
python boto3.py

# Run AFTER example  
python wrangler.py
```