# Demo 03: Excel Processing with Japanese Text Normalization

## Overview
Demonstrates processing Excel files with Japanese text, normalizing inconsistent spacing, and creating partitioned Glue tables.

## Use Case
Clean and standardize messy Excel data with inconsistent formatting, then optimize for analytics with proper partitioning.

## Files
- `boto3.py` - **BEFORE**: Manual Excel processing, text normalization, and Glue registration
- `wrangler.py` - **AFTER**: Streamlined processing with automatic Glue integration
- `employees.csv` - Sample Japanese employee data with inconsistent spacing

## Key Differences

### BEFORE (boto3.py)
- Manual Excel file reading
- Complex text normalization logic
- Manual partitioning by department
- Individual S3 uploads
- Manual Glue table creation
- ~35 lines of processing code

### AFTER (wrangler.py)
- Simplified Excel processing
- Same normalization (business logic preserved)
- Automatic partitioning and upload
- Single function for Glue registration
- ~15 lines of code

## Benefits Demonstrated
- **Simplified file handling**: Excel processing made easier
- **Preserved business logic**: Text normalization still handled
- **Automatic optimization**: Partitioning and compression handled
- **Integrated workflow**: Direct Excel to Glue table pipeline

## Data Details
The `employees.csv` contains Japanese employee data with:
- Inconsistent spacing in names, positions, and departments
- Mixed hiragana/katakana text requiring normalization
- Real-world data quality issues

## Prerequisites
- S3 bucket configured
- Glue database created
- `jaconv` library for Japanese text normalization

## Usage
```bash
# Run BEFORE example
python boto3.py

# Run AFTER example
python wrangler.py
```