# Demo 05: DynamoDB Batch Lookup Operations

## Overview
Demonstrates retrieving multiple items from DynamoDB by key and converting results to pandas DataFrames.

## Use Case
Perform fast operational lookups of movie data by ID for real-time applications and user interfaces.

## Files
- `boto3.py` - **BEFORE**: Manual batch operations with complex type conversion
- `wrangler.py` - **AFTER**: Simple key-based lookup with automatic DataFrame creation

## Key Differences

### BEFORE (boto3.py)
- Manual DynamoDB type annotations for keys (`{'S': value}`)
- Complex `batch_get_item()` request structure
- Manual handling of unprocessed keys
- Manual type conversion from DynamoDB format
- Manual DataFrame construction
- ~25 lines of type handling code

### AFTER (wrangler.py)
- Simple Python dictionaries for keys
- Automatic batch request management
- Automatic unprocessed key handling
- Automatic type conversion to pandas types
- Direct DataFrame result
- 1 function call: `wr.dynamodb.get_items()`

## Benefits Demonstrated
- **Type complexity elimination**: No DynamoDB type annotations needed
- **Automatic batch management**: Handles 100-item limits automatically
- **Error resilience**: Built-in unprocessed key retry logic
- **Direct integration**: Results directly as pandas DataFrame

## Technical Details
- **Lookup pattern**: Efficient for key-based access
- **Batch optimization**: Automatically handles DynamoDB's 100-item limit
- **Type safety**: Automatic conversion from DynamoDB types to pandas types

## Performance Notes
- **DynamoDB strength**: Excellent for key-based lookups (millisecond response)
- **DynamoDB weakness**: Would be inefficient for genre searches (requires table scan)
- **Recommendation**: Use Athena for analytical queries, DynamoDB for operational lookups

## Prerequisites
- DynamoDB table with movie data (from Demo 04)
- Proper IAM permissions for DynamoDB
- Movie IDs to lookup

## Usage
```bash
# Run BEFORE example
python boto3.py

# Run AFTER example
python wrangler.py
```