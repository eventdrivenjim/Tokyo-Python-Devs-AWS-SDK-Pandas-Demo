# Demo 04: DynamoDB Batch Write Operations

## Overview
Demonstrates writing pandas DataFrames to DynamoDB, highlighting the complexity of manual type conversion and batch management.

## Use Case
Store processed movie data in DynamoDB for fast operational lookups and real-time applications.

## Files
- `boto3.py` - **BEFORE**: Manual individual writes with complex type conversion
- `wrangler.py` - **AFTER**: Direct DataFrame to DynamoDB conversion

## Key Differences

### BEFORE (boto3.py)
- Manual DynamoDB type annotations (`{'S': value}`, `{'N': value}`)
- Individual `put_item()` calls (no batching)
- Manual rate limiting with sleep delays
- Complex error handling for throttling
- Manual success/failure tracking
- ~40 lines of type conversion and error handling

### AFTER (wrangler.py)
- Automatic type conversion from pandas to DynamoDB
- Automatic batching (25 items per request)
- Built-in retry logic and throttling management
- Automatic error handling
- 1 function call: `wr.dynamodb.put_df()`

## Benefits Demonstrated
- **Type system abstraction**: No need to understand DynamoDB type annotations
- **Batch optimization**: Automatic batching for better performance
- **Error resilience**: Built-in retry and throttling management
- **Dramatic simplification**: From 40+ lines to 1 function call

## Technical Details
- **BEFORE**: Processes 100 items individually with 10ms delays
- **AFTER**: Automatically batches into ~4 requests of 25 items each
- **Performance**: AFTER approach is significantly faster due to batching

## Prerequisites
- DynamoDB table created
- Proper IAM permissions for DynamoDB
- MovieLens movies.csv data available

## Usage
```bash
# Run BEFORE example (slower, individual writes)
python boto3.py

# Run AFTER example (faster, batched writes)
python wrangler.py
```