import psycopg2
import csv
import os

# Configurar la conexión a PostgreSQL
conn = psycopg2.connect(
    dbname="retail_db",
    user="postgres",
    password="casa1234",
    host="localhost",  # Puede ser localhost o una IP
    port="5432"  # Puerto por defecto
)

cursor = conn.cursor()

# Nombre de la tabla que queremos exportar
tabla = "Stores"
ruta_csv = "data_bda/csv/stores_data.csv"

# Crear la carpeta si no existe
os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)

# Obtener los datos de la tabla
query = f"SELECT * FROM {tabla}"
cursor.execute(query)

# Obtener nombres de columnas
column_names = [desc[0] for desc in cursor.description]

# Escribir en el archivo CSV
with open(ruta_csv, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, quoting=csv.QUOTE_NONE, delimiter=',', escapechar='\\')  
    
    # Escribir encabezado
    writer.writerow(column_names)
    
    # Limpiar datos y escribir filas
    cleaned_rows = [[str(cell).replace(',', ' ') for cell in row] for row in cursor.fetchall()]
    writer.writerows(cleaned_rows)

# Cerrar conexión
cursor.close()
conn.close()

print(f"✅ Exportación completada sin comillas ni problemas con comas: {ruta_csv}")
