import psycopg2
import random
from faker import Faker

fake = Faker()

def introduce_errors(value, error_rate=0.05):
    error_type = random.random()
    if error_type < error_rate:
        if error_type < error_rate / 3:
            return None  # Dato nulo
        elif error_type < 2 * (error_rate / 3):
            return ""  # Dato vacío
        else:
            return "ERROR"  # Error de formato
    return value

def create_table():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="retail_db",
            user="postgres",
            password="casa1234",
            port=5432
        )
        createTableString = 'CREATE TABLE IF NOT EXISTS Stores ( store_id SERIAL PRIMARY KEY, store_name VARCHAR(255), location VARCHAR(255), demographics VARCHAR(255));'
        createTableString2 = 'CREATE TABLE IF NOT EXISTS Tiendas ( store_id SERIAL PRIMARY KEY, store_name VARCHAR(255), location VARCHAR(255), demographics VARCHAR(255), Tratado VARCHAR(255), Fecha_Insercion TIMESTAMP);'

        with conn.cursor() as cur:
            cur.execute(createTableString)
            cur.execute(createTableString2)

        conn.commit()

        with conn.cursor() as cur:
            for x in range(1000):
                store_name = introduce_errors(fake.company())
                location = introduce_errors(fake.city())
                demographics = introduce_errors(fake.region())
                
                insertString = 'INSERT INTO Stores (store_name, location, demographics) VALUES (%s, %s, %s)'
                cur.execute(insertString, (store_name, location, demographics))
            conn.commit()

    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_table()
