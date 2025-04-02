from kafka import KafkaConsumer
import json

# Configurar el consumidor Kafka
consumer = KafkaConsumer(
    "sales_stream",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

print("Esperando mensajes de Kafka...")

for message in consumer:
    print(f"Recibido: {message.value}")
