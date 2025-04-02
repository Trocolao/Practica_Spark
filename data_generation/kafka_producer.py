from time import sleep
from json import dumps
from kafka import KafkaProducer
from datetime import datetime
from faker import Faker
import random

fake = Faker()

producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda x: dumps(x).encode('utf-8'))

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

while True:
    message = {
        "timestamp": introduce_errors(int(datetime.now().timestamp() * 1000)),
        "store_id": introduce_errors(random.randint(1, 100)),
        "product_id": introduce_errors(fake.uuid4()),  
        "quantity_sold": introduce_errors(random.randint(1, 20)),  
        "revenue": introduce_errors(round(random.uniform(100.0, 1000.0), 2))  
    }
    producer.send('sales_stream', value=message)
    sleep(1)
