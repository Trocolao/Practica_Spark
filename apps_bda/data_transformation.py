from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, when
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
df = spark.read \
    .format("parquet") \
    .load("s3a://sample-bucket/sales/")

df_ = spark.read \
    .format("parquet") \
    .load("s3a://sample-bucket/sales/")

# Esquema del dataframe
df.printSchema()

# 1. **Tratamiento de valores perdidos (Nulos)**

# Imputación para las columnas numéricas (rellenar con la media)
imputer = Imputer(inputCols=["quantity_sold", "revenue"], outputCols=["quantity_sold_imputed", "revenue_imputed"])
df = imputer.fit(df).transform(df)

# Opcional: Eliminar filas con valores perdidos en columnas críticas (si fuera necesario)
df = df.dropna(subset=["store_id", "product_id"])

# 2. **Eliminar duplicados**: Eliminar registros duplicados basados en el subconjunto de columnas
df = df.dropDuplicates(["store_id", "product_id", "timestamp"])

# 3. **Conversión de tipos de datos**:

# Convertir timestamp de String a Date/Time
df = df.withColumn("timestamp", col("timestamp").cast("timestamp"))

# Convertir revenue de String a Double (si es necesario)
df = df.withColumn("revenue", col("revenue").cast("double"))

# 4. **Añadir columnas de metadata**:
# Añadir columna "Tratados" (marca si fue tratado en la transformación)
df = df.withColumn("Tratados", when(col("quantity_sold").isNotNull(), "Sí").otherwise("No"))

# Añadir columna de "Fecha Inserción" (fecha UTC de la inserción)
df = df.withColumn("Fecha Inserción", current_timestamp())

# 5. **Detección y tratamiento de valores atípicos**:

# Para detectar valores atípicos, vamos a usar una técnica sencilla: el rango intercuartílico (IQR)
def detect_outliers(df, column):
    # Calcular los cuartiles
    quantiles = df.approxQuantile(column, [0.25, 0.75], 0.05)
    q1 = quantiles[0]
    q3 = quantiles[1]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return df.filter((col(column) >= lower_bound) & (col(column) <= upper_bound))

# Detectar valores atípicos en "revenue"
df = detect_outliers(df, "revenue")

# Detectar valores atípicos en "quantity_sold"
df = detect_outliers(df, "quantity_sold")

# 6. **Escribir los datos transformados en el Data Lake (S3)**:
# Guardar los datos transformados en el bucket de S3 (en formato Parquet)
df.write \
    .mode("overwrite") \
    .parquet("s3a://sample-bucket/transformed_sales/")

# Mostrar los primeros registros para verificar
df.show(10)

# Finalizar la sesión de Spark
spark.stop()
