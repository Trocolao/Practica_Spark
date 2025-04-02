from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType
aws_access_key_id='test'
aws_secret_access_key='test'
try:
    spark = SparkSession.builder \
        .appName("Streaming from Kafka") \
        .config("spark.streaming.stopGracefullyOnShutdown", True) \
        .config("spark.sql.shuffle.partitions", 4) \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localstack:4566") \
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id) \
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key) \
        .config("spark.jars.packages","org.apache.spark:spark-hadoop-cloud_2.13:3.5.1,software.amazon.awssdk:s3:2.25.11,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.driver.extraClassPath", "/opt/spark/jars/s3-2.25.11.jar") \
        .config("spark.executor.extraClassPath", "/opt/spark/jars/s3-2.25.11.jar") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
        
        
        
    df =spark  \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9093") \
    .option("subscribe", "sales_stream") \
    .load()
    

    schema = StructType() \
        .add("timestamp", IntegerType()) \
        .add("store_id", IntegerType()) \
        .add("product_id", StringType()) \
        .add("quantity_sold", IntegerType()) \
        .add("revenue", DoubleType())

    # Convert value column to JSON and apply schema
    df = df.selectExpr("CAST(value AS STRING)") \
        .select(from_json("value", schema).alias("data")) \
        .select("data.*")

    # Print schema of DataFrame for debugging
    df.printSchema()

    query = df \
        .writeStream \
        .option("path", "s3a://sample-bucket/sales") \
        .trigger(availableNow=True)\
        .option("checkpointLocation", "s3a://sample-bucket/checkopoint")\
        .outputMode("append")\
        .option('fs.s3a.committer.name', 'partitioned') \
        .option('fs.s3a.committer.staging.conflict-mode', 'replace') \
        .option("fs.s3a.fast.upload.buffer", "bytebuffer")\
        .start()

    query.awaitTermination()

except Exception as e:
        print("Error reading data from Kafka:", e)
finally:
    spark.stop()