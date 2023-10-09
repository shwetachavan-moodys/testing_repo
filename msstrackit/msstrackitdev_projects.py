## Importing necessery packages and establishing pyspark
import sys
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.conf import SparkConf
from pyspark.sql.functions import *

## establishing iceberg configurations and setting s3 warehouse path
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'iceberg_job_catalog_warehouse'])
conf = SparkConf()
conf.set("spark.sql.catalog.job_catalog.warehouse", args['iceberg_job_catalog_warehouse'])
conf.set("spark.sql.catalog.job_catalog", "org.apache.iceberg.spark.SparkCatalog")
conf.set("spark.sql.catalog.job_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
conf.set("spark.sql.catalog.job_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
conf.set("spark.sql.iceberg.handle-timestamp-without-timezone","true")



sc = SparkContext(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
logger = glueContext.get_logger()
job = Job(glueContext)
job.init(args["JOB_NAME"], args)
glue_context = GlueContext(SparkContext.getOrCreate())

logger.info(f"Time recorded before connecting to SQL server")
# Script generated for connection configuration Microsoft SQL Server
configuration1 = glue_context.extract_jdbc_conf(
    connection_name="trackit_dev_sql",
    catalog_id=None
)
logger.info(f"Time recorded before fetching source table")
df1 = glueContext.read.format("jdbc").option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver").option("url",configuration1["fullUrl"]).option("dbtable", "dbo.projects").option("user", configuration1["user"]).option("password", configuration1["password"]).load()
# Create or replace a local temporary view with above DataFrame which will be active till spark session is active.
df1.createOrReplaceTempView("projects_df")
logger.info(f"Time recorded after before data to s3")

# #Iceberg table insertion selecting data from above created temporary view.
spark.sql("""insert overwrite job_catalog.mssfinhubdb.trackitdev_projects  SELECT * from projects_df""")

logger.info(f"Time recorded after writing data to s3")
job.commit()