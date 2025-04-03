from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, when, to_date,mean, from_unixtime,lit,desc,sum,asc
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType
from pyspark.ml.feature import Imputer
import pandas as pd
import numpy as np

# Crear la sesión de Spark
spark = SparkSession.builder \
    .appName("Data Analysis") \
    .config("spark.sql.shuffle.partitions", 4) \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localstack:4566") \
    .config("spark.hadoop.fs.s3a.access.key", "test") \
    .config("spark.hadoop.fs.s3a.secret.key", "test") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()


df_sales = spark.read \
    .format("csv") \
    .option("header", "true") \
    .option("inferSchema","false") \
    .option("delimiter",",") \
    .option("pathGlobFilter","*.csv") \
    .load("s3a://sample-bucket/output_processed/")   

df_stores = spark.read \
    .format("csv") \
    .option("header", "true") \
    .option("inferSchema","false") \
    .option("delimiter",",") \
    .option("pathGlobFilter","*.csv") \
    .load("s3a://sample-bucket/stores_processed/")

#Como no se quedan los nombres y los tipos de datos los ponemos manualente
column_names = ["date", "store_id", "product_id", "quantity_sold", "revenue","Tratado","Fecha Inserción"]
column_names2 = ["store_id", "store_name", "location", "demographics","Tratado","Fecha Inserción"]

df_sales = df_sales.toDF(*column_names)
df_stores = df_stores.toDF(*column_names2)
df_stores = df_stores.drop("Tratado", "Fecha Inserción")
df_sales_stores = df_sales.join(df_stores, on="store_id", how="left")

df_sales_stores = df_sales_stores.select(
    to_date(col("date"), "yyyy-MM-dd").alias("date"),    
    col("store_id").cast("int").alias("store_id"),   
    col("product_id").cast("string").alias("product_id"),    
    col("quantity_sold").cast("int").alias("quantity_sold"),    
    col("revenue").cast("double").alias("revenue"),
    col("store_name").cast("string").alias("store_name"),
    col("location").cast("string").alias("location"),
    col("demographics").cast("string").alias("demographics")
)

#¿Qué tienda tiene los mayores ingresos totales?
df_sales_stores.groupBy("store_id", "store_name") \
    .agg(sum("revenue").alias("total_revenue")) \
    .orderBy(desc("total_revenue")) \
    .show(5)

# ¿Cuáles son los ingresos totales generados en una fecha concreta?

df_sales_stores.filter(df_sales_stores["date"] == "2023-06-17") \
    .groupBy("date") \
    .agg(sum("revenue").alias("total_revenue")) \
    .orderBy(asc("total_revenue")) \
    .show()

# ¿Qué producto tiene la mayor cantidad vendida?
df_sales_stores.groupBy("product_id") \
    .agg(sum("quantity_sold").alias("total_quantity_sold")) \
    .orderBy(desc("total_quantity_sold")) \
    .show(5)
#¿Cuáles son las regiones con mejores resultados en función de los ingresos?
df_sales_stores.groupBy("location") \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(5)

# ¿Existe alguna correlación entre la ubicación de la tienda y el rendimiento de las ventas?
df_sales_stores.groupBy("location") \
    .agg(sum("quantity_sold").alias("total_quantity_sold")) \
    .orderBy(desc("total_quantity_sold")) \
    .show(5)

# ¿Cómo varía el rendimiento de las ventas entre los distintos grupos demográficos?
df_sales_stores.groupBy("demographics") \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(5)

# ¿Existen productos específicos preferidos por determinados grupos demográficos?
df_sales_stores.groupBy("demographics", "product_id") \
    .agg(F.sum("quantity_sold").alias("total_quantity_sold")) \
    .orderBy(F.desc("total_quantity_sold")) \
    .show(5)

# ¿Cómo varía el rendimiento de las ventas a lo largo del tiempo (diariamente, semanalmente, mensualmente)?
df_sales_stores.groupBy("date") \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(5)

df_sales_stores.groupBy(F.date_format("date", "yyyy-MM").alias("month")) \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(5)

#Me ha salido un error de formato de spark que ya no acepta las semanas por lo que hago del dia del mes
df_sales_stores.groupBy(F.date_format("date", "MM-dd").alias("day_of_month")) \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(5)

# ¿Existen tendencias estacionales en las ventas?
df_sales_stores.groupBy(F.date_format("date", "yyyy-MM")) \
    .agg(F.sum("revenue").alias("total_revenue")) \
    .orderBy(F.desc("total_revenue")) \
    .show(12) 

spark.stop()
