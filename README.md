# AWS SDK for Pandas (AWSWrangler) Demo

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com/in/jimoneil)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github)](https://github.com/yourusername/aws-wrangler-demos)

This repository contains BEFORE/AFTER examples demonstrating how [AWS SDK for Pandas (awswrangler)](https://github.com/aws/aws-sdk-pandas) simplifies common data processing workflows compared to using boto3 and pandas directly.

## About AWS SDK for Pandas

[AWS SDK for Pandas](https://github.com/aws/aws-sdk-pandas) is an **official open-source Python library developed and maintained by AWS** that extends pandas to work seamlessly with AWS data services.

**Key Resources:**
- **GitHub Repository**: https://github.com/aws/aws-sdk-pandas
- **Documentation**: https://aws-sdk-pandas.readthedocs.io/
- **PyPI Package**: https://pypi.org/project/awswrangler/

**Why AWS Built This:**
- Simplifies complex AWS data workflows
- Reduces boilerplate code by 80-90%
- Provides pandas-native interface to AWS services
- Maintained by AWS with regular updates and new features

## Dataset: MovieLens

These demos use the MovieLens dataset, a popular movie recommendation dataset containing movie information and user ratings.

### Getting the MovieLens Data

1. **Download the dataset:**
   ```bash
   # Option 1: Using wget
   wget https://files.grouplens.org/datasets/movielens/ml-25m.zip
   
   # Option 2: Using curl
   curl -O https://files.grouplens.org/datasets/movielens/ml-25m.zip
   
   unzip ml-25m.zip
   
   # If unzip is not available:
   # Ubuntu/Debian: sudo apt install unzip
   # RHEL/CentOS: sudo yum install unzip  
   # macOS: Available by default
   # Windows: Use built-in zip extraction or winget install 7zip.7zip
   ```

2. **Key files and columns:**

   **movies.csv** (62,423 movies)
   - `movieId` - Unique movie identifier (integer, 1-193609)
   - `title` - Movie title with release year in parentheses (string)
     - Format: "Movie Name (YYYY)"
     - Example: "Toy Story (1995)", "The Matrix (1999)"
     - Some titles may have additional info like "(TV Series)" or "(Video)"
   - `genres` - Pipe-separated list of genres (string)
     - Multiple genres separated by "|" character
     - Example: "Action|Adventure|Sci-Fi"
     - Movies with no genre info show "(no genres listed)"
     - Can contain 1-8 genres per movie

   **ratings.csv** (25,000,095 ratings)
   - `userId` - Unique user identifier (integer)
   - `movieId` - Movie identifier matching movies.csv
   - `rating` - Rating on 5-star scale (0.5, 1.0, 1.5, ..., 5.0)
   - `timestamp` - Unix timestamp when rating was given

   **tags.csv** (1,093,360 tags)
   - `userId` - User identifier
   - `movieId` - Movie identifier
   - `tag` - User-generated tag/keyword
   - `timestamp` - Unix timestamp when tag was applied

   **links.csv** (62,423 links)
   - `movieId` - MovieLens movie identifier
   - `imdbId` - IMDb movie identifier
   - `tmdbId` - The Movie Database (TMDb) identifier

3. **Upload to S3:**
   ```bash
   # Only movies.csv is required for these demos
   aws s3 cp ml-25m/movies.csv s3://your-bucket/movies.csv
   
   # Optional - other files for extended analysis
   aws s3 cp ml-25m/ratings.csv s3://your-bucket/ratings.csv
   aws s3 cp ml-25m/tags.csv s3://your-bucket/tags.csv
   aws s3 cp ml-25m/links.csv s3://your-bucket/links.csv
   ```

**Note:** These demos primarily use `movies.csv`. The other files are provided for reference and extended analysis.

### Sample Data Structure

**movies.csv:**
```csv
movieId,title,genres
1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy
2,Jumanji (1995),Adventure|Children|Fantasy
3,Grumpier Old Men (1995),Comedy|Romance
```

**ratings.csv:**
```csv
userId,movieId,rating,timestamp
1,1,4.0,964982703
1,3,4.0,964981247
1,6,4.0,964982224
```

**Available Genres:**
Action, Adventure, Animation, Children, Comedy, Crime, Documentary, Drama, Fantasy, Film-Noir, Horror, Musical, Mystery, Romance, Sci-Fi, Thriller, War, Western, IMAX, (no genres listed)

## AWS Account Requirements

### AWS Account Setup

These demos require an AWS account to access AWS services.

1. **Create AWS Account (if needed):**
   - AWS account registration is free at https://aws.amazon.com
   - **Important:** You will need to provide a valid credit card during registration
   - **Note:** AWS may place a temporary authorization hold on your card for verification

2. **Cost Considerations:**
   - Many AWS services offer a **Free Tier** for new accounts (12 months)
   - **WARNING:** Creating and running these demos **MAY incur charges** if you exceed free tier limits
   - Services used: S3, DynamoDB, Glue, Athena - check current free tier limits
   - **Recommendation:** Monitor your AWS billing dashboard regularly
   - **Best Practice:** Delete resources after completing demos to avoid ongoing charges

3. **Install AWS CLI:**

These demos require the AWS CLI for deploying infrastructure and managing resources.

**Local Development:**
- **macOS:** `brew install awscli` or download from [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Windows:** Download installer from AWS or use `winget install Amazon.AWSCLI`
- **Linux:** `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install`

**Verify installation:**
```bash
aws --version
```

**Container Development:**
AWS CLI is pre-installed in the Docker container - no additional installation needed.

4. **Configure AWS Credentials:**

**Local Development:**
```bash
aws configure
```
Enter your Access Key ID, Secret Access Key, region, and output format.

**Container Development:**
AWS credentials are automatically mounted when using the Makefile commands.

**Note:** On Windows with WSL2, ensure AWS CLI is configured within WSL2, not Windows.

5. **Configure Environment Variables:**
   
   Edit the `.env` file with your resource names:
   ```bash
   # Edit the .env file with your preferred editor
   code .env
   # or
   nano .env
   ```
   
   Update the values in `.env`:
   ```bash
   export ENVIRONMENT="demo"
   export S3_BUCKET_BASE="<your-unique-bucket-base>"
   export S3_BUCKET_NAME="${S3_BUCKET_BASE}-${ENVIRONMENT}"
   export DYNAMODB_TABLE_NAME="movies-demo"
   export GLUE_DATABASE_NAME="movielens-demo"
   export ATHENA_RESULT_LOCATION="s3://${S3_BUCKET_NAME}/athena-results/"
   ```
   
   **Local Development:**
   Load the environment variables:
   ```bash
   source .env
   ```
   
   **Container Development:**
   Environment variables are automatically loaded by the Makefile.

**Container Development - Start Container:**
```bash
# Start container with mounted files (automatically builds if needed)
make shell

# Your local directory is now mounted as /app in the container
# Continue with infrastructure deployment inside the container
```

6. **Deploy Infrastructure:**
   ```bash
   # Deploy the CloudFormation template to create required AWS resources
   # Uses environment variables from .env file
   aws cloudformation deploy \
     --template-file cloudformation_template.yaml \
     --stack-name wrangler-demo-stack \
     --parameter-overrides BucketName=${S3_BUCKET_BASE} Environment=${ENVIRONMENT}
   ```

### Required IAM Permissions

Your AWS credentials need these minimum permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "glue:CreateTable",
                "glue:GetTable",
                "glue:UpdateTable",
                "athena:StartQueryExecution",
                "athena:GetQueryResults",
                "athena:GetQueryExecution",
                "dynamodb:PutItem",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:CreateTable"
            ],
            "Resource": "*"
        }
    ]
}
```

**Security Best Practices:**
- Use IAM roles when running on AWS infrastructure
- Apply principle of least privilege
- Never hardcode credentials in source code
- Use temporary credentials when possible

## Demo Files

These demos show the power of [awswrangler](https://github.com/aws/aws-sdk-pandas) compared to manual boto3 implementations.

**All demos use the `movies.csv` file as the primary dataset.**

### Demo Execution Order

**Important:** Run the demos in this order for best results:

1. **01_csv_to_parquet.py** - Creates the Glue table needed for Athena queries
2. **02_athena_query.py** - Queries the table created in demo 01
3. **04_dynamodb_write.py** - Writes data to DynamoDB table
4. **05_dynamodb_lookup.py** - Reads data from DynamoDB table created in demo 04
5. **06_athena_to_dynamodb_etl.py** - ETL pipeline from Athena to DynamoDB
6. **03_excel_to_glue.py** - Independent demo (uses different dataset)erent dataset)

**Note:** Demo 02 will fail if demo 01 hasn't been run first, as it depends on the Glue table being created.

**Independent Demos:**
- **03_excel_to_glue.py** - Uses different dataset, can run standalone
- **06_athena_to_dynamodb_etl.py** - Requires demos 01+02 (uses Athena table), creates separate DynamoDB table

## Project Structure

```
aws-wrangler-demos/
├── demos/                    # Demo Python scripts
│   ├── 01_csv_to_parquet.py
│   ├── 02_athena_query.py
│   ├── 03_excel_to_glue.py
│   ├── 04_dynamodb_write.py
│   ├── 05_dynamodb_lookup.py
│   └── 06_athena_to_dynamodb_etl.py
├── .env                     # Environment variables configuration
├── .gitignore              # Git ignore rules
├── cloudformation_template.yaml  # AWS infrastructure template
├── Dockerfile              # Container configuration
├── makefile                # Container management commands
├── pyproject.toml          # Python project configuration
├── uv.lock                 # Dependency lock file
└── README.md              # This documentation
```

**Key directories:**
- **`demos/`** - Contains all Python demo scripts
- **Root directory** - Infrastructure files (.env, CloudFormation, Makefile, Docker)

### 01_csv_to_parquet.py
**Purpose:** Convert CSV to partitioned Parquet and register with AWS Glue
- **BEFORE:** Manual partitioning, S3 upload, and Glue registration
- **AFTER:** Single function call handles everything

### 02_athena_query.py
**Purpose:** Query data with Amazon Athena and return results as DataFrame
- **BEFORE:** Manual query execution, polling, and result retrieval
- **AFTER:** Direct SQL query to DataFrame conversion

### 03_excel_to_glue.py
**Purpose:** Process Japanese Excel data and create partitioned Glue table
- **BEFORE:** Manual text standardization, partitioning, and Glue registration
- **AFTER:** Streamlined processing with automatic Glue integration

### 04_dynamodb_write.py
**Purpose:** Write DataFrame to DynamoDB table
- **BEFORE:** Manual batch operations with error handling
- **AFTER:** Direct DataFrame to DynamoDB conversion

### 05_dynamodb_lookup.py
**Purpose:** Lookup items from DynamoDB and export to Parquet
- **BEFORE:** Manual key formatting, type conversion, and DataFrame creation
- **AFTER:** Simple key-based lookup with automatic type handling

### 06_athena_to_dynamodb_etl.py
**Purpose:** ETL pipeline from Athena analytical queries to DynamoDB for fast operational lookups
- **BEFORE:** Manual Athena query execution, result processing, and DynamoDB batch writes
- **AFTER:** Streamlined ETL with automatic query execution and data transfer

## Prerequisites

### Option 1: Local Installation

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **AWS Configuration:**
   - Configure AWS credentials (`aws configure`)
   - Ensure appropriate IAM permissions for S3, Glue, Athena, and DynamoDB

### Option 2: Docker Container

Use the provided Makefile for containerized development:

1. **Build and run with Docker (default):**
   ```bash
   make build
   make shell
   ```

2. **Or use Podman instead:**
   
   **Option A - Override per command:**
   ```bash
   make build CONTAINER_ENGINE=podman
   make shell CONTAINER_ENGINE=podman
   ```
   
   **Option B - Edit Makefile permanently:**
   ```bash
   # Change line 4 in Makefile from:
   CONTAINER_ENGINE=docker
   # To:
   CONTAINER_ENGINE=podman
   ```
   Then use normal commands:
   ```bash
   make build
   make shell
   ```

3. **Available Makefile targets:**
   - `make build` - Build the container image
   - `make shell` - Run interactive shell with current directory mounted
   - `make inspect` - Run container for inspection
   - `make rm` - Remove stopped local container (cleanup)

**Container Features:**
- Pre-installed dependencies from `pyproject.toml`
- AWS CLI pre-installed for infrastructure deployment
- AWS region set to `ap-northeast-1` by default
- Support for both Docker and Podman (change `CONTAINER_ENGINE` variable)

**Note:** AWS CLI is included for demo convenience only. In production containers, use AWS SDKs (like awswrangler) instead of CLI tools for better security and smaller image size.

### Makefile Commands

The project includes a Makefile for easy container management:

**Available targets:**
- `make build` - Build the container image from Dockerfile
- `make shell` - Run interactive shell **with local files mounted** (for development)
- `make inspect` - Run interactive shell **without local files** (simulates production/ECS)
- `make rm` - Remove stopped local container (cleanup)

**Important distinction:**
- **`make shell`** - Mounts your current directory to `/app` in the container
  - Local file changes are immediately available in container
  - Use this for running demos and development
  - Your `.env` file and demo scripts are accessible

- **`make inspect`** - Uses only files built into the container image
  - No local directory mounting (simulates ECS/production deployment)
  - Only files copied during `docker build` are available
  - Use this to test production-like container behavior

**Container Engine Support:**
To use Podman instead of Docker, edit the Makefile:
```makefile
# Change line 4 from:
CONTAINER_ENGINE=docker
# To:
CONTAINER_ENGINE=podman
```

### AWS Resources Required

- S3 bucket for data storage
- Glue database (e.g., "movielens-demo")
- DynamoDB table (e.g., "movies-demo")
- Athena query result location

## Key Benefits Demonstrated

- **Reduced Code Complexity:** 10-20 lines vs 2-3 lines
- **Automatic Error Handling:** Built-in retries and error management
- **Type Conversion:** Automatic handling of AWS service data types
- **Integration:** Seamless connection between AWS services
- **Performance:** Optimized operations for large datasets

## Running the Demos

1. Update bucket names and table names in the code
2. Ensure your AWS resources are created
3. Run individual demo files to see the differences

Each demo shows the manual complexity required with boto3/pandas versus the simplified approach with AWS SDK for Pandas.

## Cleanup Resources

**Important:** To avoid ongoing charges, delete all AWS resources after completing the demos.

### Option 1: Delete CloudFormation Stack (Recommended)

This removes all resources created by the template:

```bash
# First, empty the S3 bucket (required before stack deletion)
aws s3 rm s3://${S3_BUCKET_NAME} --recursive

# Then delete the entire stack and all its resources
aws cloudformation delete-stack --stack-name wrangler-demo-stack

# Monitor deletion progress
aws cloudformation describe-stacks --stack-name wrangler-demo-stack
```

**Important:** S3 buckets cannot be deleted if they contain objects. You must empty the bucket first.

**Note:** CloudFormation automatically deletes the DynamoDB table, Glue database, and all other resources - no manual cleanup needed.

### Option 2: Manual Resource Cleanup

#### S3 Bucket Cleanup

**AWS Console:**
1. Go to S3 Console → Select your bucket
2. Click "Empty" → Type "permanently delete" → Confirm
3. Click "Delete" → Type bucket name → Confirm

**AWS CLI:**
```bash
# Remove all objects from bucket (CloudFormation will delete the empty bucket)
aws s3 rm s3://${S3_BUCKET_NAME} --recursive
```

### Verify Cleanup

Check that all resources are deleted:
```bash
# Check S3 buckets
aws s3 ls

# Check DynamoDB tables
aws dynamodb list-tables

# Check Glue databases
aws glue get-databases

# Check CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

## Connect

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/jimoneil)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/yourusername/aws-wrangler-demos)

## Project Structure

```
aws-wrangler-demos/
├── demos/                    # Demo Python scripts and container files
│   ├── 01_csv_to_parquet.py
│   ├── 02_athena_query.py
│   ├── 03_excel_to_glue.py
│   ├── 04_dynamodb_write.py
│   ├── 05_dynamodb_lookup.py
│   ├── Dockerfile
│   ├── .dockerignore        # Docker build context exclusions
│   ├── requirements.txt     # Python dependencies (compiled)
│   └── requirements.in      # Python dependencies (source)
├── .env                     # Environment variables configuration
├── .gitignore              # Git ignore rules
├── cloudformation_template.yaml  # AWS infrastructure template
├── makefile                # Container management commands
└── README.md              # This documentation
```

**Key directories:**
- **`demos/`** - Contains all Python demo scripts and container configuration
- **Root directory** - Infrastructure files (.env, CloudFormation, Makefile)

### 01_csv_to_parquet.py
**Purpose:** Convert CSV to partitioned Parquet and register with AWS Glue
- **BEFORE:** Manual partitioning, S3 upload, and Glue registration
- **AFTER:** Single function call handles everything

### 02_athena_query.py
**Purpose:** Query data with Amazon Athena and return results as DataFrame
- **BEFORE:** Manual query execution, polling, and result retrieval
- **AFTER:** Direct SQL query to DataFrame conversion

### 03_excel_to_glue.py
**Purpose:** Process Japanese Excel data and create partitioned Glue table
- **BEFORE:** Manual text standardization, partitioning, and Glue registration
- **AFTER:** Streamlined processing with automatic Glue integration

### 05_dynamodb_write.py
**Purpose:** Write DataFrame to DynamoDB table
- **BEFORE:** Manual batch operations with error handling
- **AFTER:** Direct DataFrame to DynamoDB conversion

### 05_dynamodb_lookup.py
**Purpose:** Lookup items from DynamoDB and export to Parquet
- **BEFORE:** Manual key formatting, type conversion, and DataFrame creation
- **AFTER:** Simple key-based lookup with automatic type handling

## Prerequisites

### Option 1: Local Installation

1. **Install dependencies:**
   ```bash
   pip install -r demos/requirements.txt
   ```

2. **AWS Configuration:**
   - Configure AWS credentials (`aws configure`)
   - Ensure appropriate IAM permissions for S3, Glue, Athena, and DynamoDB

### Option 2: Docker Container

Use the provided Makefile for containerized development:

1. **Build and run with Docker (default):**
   ```bash
   make build
   make shell
   ```

2. **Or use Podman instead:**
   
   **Option A - Override per command:**
   ```bash
   make build CONTAINER_ENGINE=podman
   make shell CONTAINER_ENGINE=podman
   ```
   
   **Option B - Edit Makefile permanently:**
   ```bash
   # Change line 4 in Makefile from:
   CONTAINER_ENGINE=docker
   # To:
   CONTAINER_ENGINE=podman
   ```
   Then use normal commands:
   ```bash
   make build
   make shell
   ```

3. **Available Makefile targets:**
   - `make build` - Build the container image
   - `make shell` - Run interactive shell with current directory mounted
   - `make inspect` - Run container for inspection
   - `make rm` - Remove stopped local container (cleanup)

**Container Features:**
- Pre-installed dependencies from `demos/requirements.in`
- AWS CLI pre-installed for infrastructure deployment
- AWS region set to `ap-northeast-1` by default
- Support for both Docker and Podman (change `CONTAINER_ENGINE` variable)

**Note:** AWS CLI is included for demo convenience only. In production containers, use AWS SDKs (like awswrangler) instead of CLI tools for better security and smaller image size.

### Makefile Commands

The project includes a Makefile for easy container management:

**Available targets:**
- `make build` - Build the container image from Dockerfile
- `make shell` - Run interactive shell **with local files mounted** (for development)
- `make inspect` - Run interactive shell **without local files** (simulates production/ECS)
- `make rm` - Remove stopped local container (cleanup)

**Important distinction:**
- **`make shell`** - Mounts your current directory to `/app` in the container
  - Local file changes are immediately available in container
  - Use this for running demos and development
  - Your `.env` file and demo scripts are accessible

- **`make inspect`** - Uses only files built into the container image
  - No local directory mounting (simulates ECS/production deployment)
  - Only files copied during `docker build` are available
  - Use this to test production-like container behavior

**Container Engine Support:**
To use Podman instead of Docker, edit the Makefile:
```makefile
# Change line 4 from:
CONTAINER_ENGINE=docker
# To:
CONTAINER_ENGINE=podman
```

### AWS Resources Required

- S3 bucket for data storage
- Glue database (e.g., "movielens", "company")
- DynamoDB table (e.g., "movies")
- Athena query result location

## Key Benefits Demonstrated

- **Reduced Code Complexity:** 10-20 lines vs 2-3 lines
- **Automatic Error Handling:** Built-in retries and error management
- **Type Conversion:** Automatic handling of AWS service data types
- **Integration:** Seamless connection between AWS services
- **Performance:** Optimized operations for large datasets

## Running the Demos

1. Update bucket names and table names in the code
2. Ensure your AWS resources are created
3. Run individual demo files to see the differences

Each demo shows the manual complexity required with boto3/pandas versus the simplified approach with AWS SDK for Pandas.

## Cleanup Resources

**Important:** To avoid ongoing charges, delete all AWS resources after completing the demos.

### Option 1: Delete CloudFormation Stack (Recommended)

This removes all resources created by the template:

```bash
# First, empty the S3 bucket (required before stack deletion)
aws s3 rm s3://${S3_BUCKET_NAME} --recursive

# Then delete the entire stack and all its resources
aws cloudformation delete-stack --stack-name wrangler-demo-stack

# Monitor deletion progress
aws cloudformation describe-stacks --stack-name wrangler-demo-stack
```

**Important:** S3 buckets cannot be deleted if they contain objects. You must empty the bucket first.

**Note:** CloudFormation automatically deletes the DynamoDB table, Glue database, and all other resources - no manual cleanup needed.

### Option 2: Manual Resource Cleanup

#### S3 Bucket Cleanup

**AWS Console:**
1. Go to S3 Console → Select your bucket
2. Click "Empty" → Type "permanently delete" → Confirm
3. Click "Delete" → Type bucket name → Confirm

**AWS CLI:**
```bash
# Remove all objects from bucket (CloudFormation will delete the empty bucket)
aws s3 rm s3://${S3_BUCKET_NAME} --recursive
```

### Verify Cleanup

Check that all resources are deleted:
```bash
# Check S3 buckets
aws s3 ls

# Check DynamoDB tables
aws dynamodb list-tables

# Check Glue databases
aws glue get-databases

# Check CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

## Connect

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/jimoneil)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/yourusername/aws-wrangler-demos)