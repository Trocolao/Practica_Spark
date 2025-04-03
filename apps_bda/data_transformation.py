from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, when, to_date,mean, from_unixtime,lit
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StringType, IntegerType, DoubleType
from pyspark.ml.feature import Imputer
import pandas as pd
import numpy as np

# Crear la sesión de Spark
spark = SparkSession.builder \
    .appName("Data Transformation") \
    .config("spark.sql.shuffle.partitions", 4) \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localstack:4566") \
    .config("spark.hadoop.fs.s3a.access.key", "test") \
    .config("spark.hadoop.fs.s3a.secret.key", "test") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Leer datos desde el bucket S3
df_csv = spark.read \
    .format("csv") \
    .option("header", "false") \
    .option("inferSchema","false") \
    .option("delimiter",",") \
    .option("pathGlobFilter","*.csv") \
    .load("s3a://sample-bucket/output/")   

df_kafka = spark.read \
    .format("csv") \
    .option("header", "false") \
    .option("inferSchema","false") \
    .option("delimiter",",") \
    .option("pathGlobFilter","*.csv") \
    .load("s3a://sample-bucket/sales_data/")
   
df_postgres = spark.read \
    .format("csv") \
    .option("header", "false") \
    .option("inferSchema","false") \
    .option("delimiter",",") \
    .option("pathGlobFilter","*.csv") \
    .load("s3a://sample-bucket/stores/")   
  
# Esquema del dataframe
# Leer el archivo CSV sin usar la primera fila como encabezado
# Definir manualmente los nombres de las columnas
column_names = ["date", "store_id", "product_id", "quantity_sold", "revenue"]
column_names2 = ["store_id", "store_name", "location", "demographics"]
numeric_columns = ["quantity_sold", "revenue"]

df_csv = df_csv.toDF(*column_names)
df_kafka = df_kafka.toDF(*column_names)
df_postgres = df_postgres.toDF(*column_names2)

#Conversión de los datos a los valores que nos piden

df_csv = df_csv.select(
    to_date(col("date"), "yyyy-MM-dd").alias("date"),    
    col("store_id").cast("int").alias("store_id"),   
    col("product_id").cast("string").alias("product_id"),    
    col("quantity_sold").cast("int").alias("quantity_sold"),    
    col("revenue").cast("double").alias("revenue")
)

df_kafka = df_kafka.select(
    (col("date").cast("double")).alias("date"),  # Aplica from_unixtime correctamente
    col("store_id").cast("int").alias("store_id"),   
    col("product_id").cast("string").alias("product_id"),    
    col("quantity_sold").cast("int").alias("quantity_sold"),    
    col("revenue").cast("double").alias("revenue")
)

df_kafka = df_kafka.withColumn("date", to_date(from_unixtime(col("date").cast("double"))))

df_postgres = df_postgres.select(
    col("store_id").cast("int").alias("store_id"),   
    col("store_name").cast("string").alias("store_name"),    
    col("location").cast("string").alias("location"),    
    col("demographics").cast("string").alias("demographics")
)

#Añadimos estas columnas ya que al cambiar el tipo de dato a todos todos los datos han sido tratados
def anadir_columnas(df):  
    # Añadir la columna 'Fecha Inserción' con la fecha actual en formato UTC
    df = df.withColumn("Tratados", lit("Sí"))
    df = df.withColumn("Fecha Inserción", current_timestamp())
    return df

df_csv=anadir_columnas(df_csv)
df_kafka=anadir_columnas(df_kafka)
df_postgres=anadir_columnas(df_postgres)

df_csv = df_csv.filter(
    (col("store_id").isNotNull()) &  # Elimina filas con store_id nulo
    (col("date").isNotNull()) &  # Elimina filas con store_id nulo
    (col("product_id").isNotNull())&
    (col("product_id")!="ERROR")&
    (col("product_id")!="INVALID")
)

df_kafka = df_kafka.filter(
    (col("store_id").isNotNull()) &
    (col("date").isNotNull()) &  # Elimina filas con store_id nulo
    (col("product_id").isNotNull())&
    (col("product_id")!="ERROR")&
    (col("product_id")!="INVALID")
)

df_postgres = df_postgres.filter(
    (col("store_id").isNotNull())
)

#Ahora vamos a rellenar los valores numéricos con la media
mean_quantity = df_csv.select(mean(col("quantity_sold"))).collect()[0][0]
mean_revenue = df_csv.select(mean(col("revenue"))).collect()[0][0]

df_csv = df_csv.fillna({"quantity_sold": mean_quantity, "revenue": mean_revenue})

#En el otro csv también
mean_quantity_2 = df_kafka.select(mean(col("quantity_sold"))).collect()[0][0]
mean_revenue_2 = df_kafka.select(mean(col("revenue"))).collect()[0][0]

df_kafka = df_kafka.fillna({"quantity_sold": mean_quantity_2, "revenue": mean_revenue_2})

#Eliminar duplicados

def get_mode(df, column_name):
    filtered_df = df.filter(
        (df[column_name] != "ERROR") & 
        (df[column_name].isNotNull()) & 
        (df[column_name] != "None")
    )
    
    # Obtener los valores más frecuentes de la columna filtrada
    mode_df = filtered_df.groupBy(column_name).count().orderBy('count', ascending=False).limit(1)
    mode = mode_df.collect()[0][0]  # Obtener el valor más frecuente
    return mode

# Obtener la moda de la columna 'product_id'
mode_value_location = get_mode(df_postgres, 'location')
mode_value_demographics = get_mode(df_postgres, 'demographics')
mode_value_store = get_mode(df_postgres, 'store_name')
# Reemplazar los valores nulos, vacíos o 'ERROR' con la moda de la columna
df_postgres = df_postgres.withColumn(
    "location", 
    when((col("location").isNull()) | (col("location") == "")| (col("location") == "None") | (col("location") == "ERROR"), mode_value_location).otherwise(col("location"))
)
df_postgres = df_postgres.withColumn(
    "demographics", 
    when((col("demographics").isNull()) | (col("demographics") == "") |(col("demographics") == "None") | (col("demographics") == "ERROR"), mode_value_demographics).otherwise(col("demographics"))
)
df_postgres = df_postgres.withColumn(
    "store_name", 
    when((col("store_name").isNull()) | (col("store_name") == "") |(col("location") == "None") | (col("store_name") == "ERROR"), mode_value_store).otherwise(col("store_name"))
)
def tratar_valores_atipicos(df, columnas):

    for columna in columnas:
        quantiles = df.approxQuantile(columna, [0.25, 0.75], 0.05)
        Q1, Q3 = quantiles[0], quantiles[1]

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        mean_value = df.select(mean(col(columna))).collect()[0][0]

        df = df.withColumn(
            columna,
            when((col(columna) < lower_bound) | (col(columna) > upper_bound), mean_value)
            .otherwise(col(columna))
        )
    return df

df_csv=tratar_valores_atipicos(df_csv,numeric_columns)
df_kafka=tratar_valores_atipicos(df_kafka,numeric_columns)

df_csv.printSchema()
df_csv.show(5)

df_kafka.printSchema()
df_kafka.show(5)

df_postgres.printSchema()
df_postgres.show(5)

df_combined = df_csv.union(df_kafka)
df_combined = df_combined.dropDuplicates(["store_id", "product_id", "date"])
df_combined.printSchema()
df_combined.show(5)

df_combined \
    .write \
    .option('fs.s3a.committer.name', 'partitioned') \
    .option('fs.s3a.committer.staging.conflict-mode', 'replace') \
    .option("fs.s3a.fast.upload.buffer", "bytebuffer")\
    .mode('overwrite') \
    .csv(path='s3a://sample-bucket/sales_processed', sep=',')
df_postgres \
    .write \
    .option('fs.s3a.committer.name', 'partitioned') \
    .option('fs.s3a.committer.staging.conflict-mode', 'replace') \
    .option("fs.s3a.fast.upload.buffer", "bytebuffer")\
    .mode('overwrite') \
    .csv(path='s3a://sample-bucket/stores_processed', sep=',')

spark.stop()
