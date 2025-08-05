# AFTER: Query Athena with awswrangler
import awswrangler as wr
import logging
from datetime import datetime

# Configure logging for AFTER section
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GLUE_DATABASE_NAME = os.environ.get('GLUE_DATABASE_NAME', 'movielens')
ATHENA_RESULT_LOCATION = os.environ.get('ATHENA_RESULT_LOCATION')

# Example 1: Original query - movies from 1995
# Matches the BEFORE example for direct comparison
df_1995 = wr.athena.read_sql_query(
    sql="SELECT title, genres FROM movies WHERE release_year = 1995",
    database=GLUE_DATABASE_NAME
)

print(df.head(10))