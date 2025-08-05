# Demo 02: Athena Query Execution

## Overview
Demonstrates executing SQL queries against AWS Athena and retrieving results as pandas DataFrames.

## Use Case
Query large datasets stored in S3 using SQL without managing infrastructure or handling async execution complexity.

## Files
- `boto3.py` - **BEFORE**: Manual query execution, polling, and result retrieval
- `wrangler.py` - **AFTER**: Direct SQL to DataFrame conversion

## Key Differences

### BEFORE (boto3.py)
- Manual query execution with `start_query_execution()`
- Polling loop to check query status
- Manual result retrieval from S3
- Error state handling
- ~15 lines of async management code

### AFTER (wrangler.py)
- Direct SQL execution: `wr.athena.read_sql_query()`
- Automatic async handling
- Direct DataFrame result
- Built-in error management
- 1 function call

## Benefits Demonstrated
- **Async complexity elimination**: No manual polling required
- **Direct integration**: SQL results directly to pandas DataFrame
- **Error handling**: Automatic retry and failure management
- **Simplified workflow**: Focus on SQL logic, not execution mechanics

## Prerequisites
- Athena configured with result location
- Glue database with movies table (from Demo 01)
- Proper IAM permissions for Athena

## Usage
```bash
# Run BEFORE example
python boto3.py

# Run AFTER example
python wrangler.py
```