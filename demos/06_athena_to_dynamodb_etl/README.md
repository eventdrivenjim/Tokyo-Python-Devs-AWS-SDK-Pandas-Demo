# Demo 06: Athena to DynamoDB ETL Pipeline

## Overview
Demonstrates a complete ETL pipeline that queries analytical data from Athena and loads it into DynamoDB for fast operational access.

## Use Case
Transform analytical movie data (stored in S3/Athena) into optimized operational lookups (DynamoDB) for real-time applications.

## Files
- `boto3.py` - **BEFORE**: Manual multi-step ETL with async handling
- `wrangler.py` - **AFTER**: Streamlined 2-function ETL pipeline

## Key Differences

### BEFORE (boto3.py)
- Manual Athena query execution and polling
- Manual S3 result retrieval
- Manual data transformation for DynamoDB
- Manual batch write operations with error handling
- Complex async workflow management
- ~50 lines of ETL orchestration

### AFTER (wrangler.py)
- Single function for Athena query: `wr.athena.read_sql_query()`
- Single function for DynamoDB write: `wr.dynamodb.put_df()`
- Automatic async handling
- Automatic data type conversion
- 2 function calls for complete ETL

## Benefits Demonstrated
- **ETL simplification**: Complex pipeline reduced to 2 function calls
- **Async abstraction**: No manual polling or status checking
- **Error handling**: Built-in retry and failure management
- **Type conversion**: Automatic pandas to DynamoDB type mapping

## Architecture Pattern
This demonstrates a common AWS data architecture:
- **Analytical layer**: S3 + Athena for complex queries and aggregations
- **Operational layer**: DynamoDB for fast key-based lookups
- **ETL bridge**: Transfer curated analytical results to operational store

## Data Flow
1. **Source**: Movies data in S3 (partitioned Parquet)
2. **Analytics**: Athena queries for popular genres and eras
3. **Transform**: Filter and categorize movies (Modern vs Classic)
4. **Load**: Store results in DynamoDB for fast API access

## Prerequisites
- Athena configured with movies table (from Demo 01)
- DynamoDB table for ETL results
- Proper IAM permissions for both services

## Usage
```bash
# Run BEFORE example (complex multi-step ETL)
python boto3.py

# Run AFTER example (streamlined 2-step ETL)
python wrangler.py
```

## Performance Comparison
- **BEFORE**: ~50 lines, manual error handling, complex async management
- **AFTER**: ~10 lines, automatic error handling, simplified workflow