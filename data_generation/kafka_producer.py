from time import sleep
from json import dumps
from kafka import KafkaProducer
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()

# Inicialización del productor de Kafka
producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda x: dumps(x).encode('utf-8'))

# Función para introducir errores aleatorios
def introduce_errors(value, error_rate=0.1):
    error_type = random.random()
    if error_type < error_rate:
        if error_type < error_rate / 3:
            return None  # Dato nulo
        elif error_type < 2 * (error_rate / 3):
            return ""  # Dato vacío
        else:
            return "ERROR"  # Error de formato
    return value

# Función para generar timestamps aleatorios dentro de un rango
def random_timestamp(start_date, end_date):
    start_timestamp = int(start_date.timestamp())  # Convertir fecha de inicio a timestamp (segundos)
    end_timestamp = int(end_date.timestamp())  # Convertir fecha de fin a timestamp (segundos)
    return random.randint(start_timestamp, end_timestamp)

# Rango de fechas: entre 1 de enero de 2020 y la fecha actual
start_date = datetime(2023, 1, 1)
end_date = datetime.now()

while True:
    # Generar un mensaje con valores aleatorios
    message = {
        "timestamp": introduce_errors(random_timestamp(start_date, end_date)),  # Timestamp aleatorio
        "store_id": introduce_errors(random.randint(1, 100)),  # ID de tienda aleatorio
        "product_id": introduce_errors(fake.uuid4()[:8]),  # ID de producto aleatorio
        "quantity_sold": introduce_errors(random.randint(1, 20)),  # Cantidad vendida aleatoria
        "revenue": introduce_errors(round(random.uniform(100.0, 1000.0), 2))  # Ingreso aleatorio
    }
    
    # Enviar el mensaje al topic 'sales_stream' de Kafka
    producer.send('sales_stream', value=message)
    sleep(1)
