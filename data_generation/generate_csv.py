import pandas as pd
import random
import os
from faker import Faker

fake = Faker()

# Número de registros
num_records = 1000

# Asegurar que el directorio de salida existe
output_dir = "data_bda/csv/"
os.makedirs(output_dir, exist_ok=True)

def introduce_errors(value, error_rate=0.1):
    error_type = random.random()
    if error_type < error_rate:
        if error_type < error_rate / 3:
            return None 
        elif error_type < 2 * (error_rate / 3):
            return ""  
        else:
            return "ERROR"  
    return value

data = {
    "date": [introduce_errors(fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d')) for _ in range(num_records)],
    "store_id": [introduce_errors(str(random.randint(1, 100)) if random.random() > 0.05 else "XX") for _ in range(num_records)],
    "product_id": [introduce_errors(fake.uuid4()[:4] if random.random() > 0.05 else "INVALID") for _ in range(num_records)],
    "quantity_sold": [introduce_errors(str(random.randint(1, 50)) if random.random() > 0.05 else "NaN") for _ in range(num_records)],
    "revenue": [introduce_errors(str(round(random.uniform(5, 500), 2)) if random.random() > 0.05 else "0.0.0") for _ in range(num_records)]
}

df = pd.DataFrame(data)

df.to_csv(os.path.join(output_dir, "sales_data.csv"), index=False)

print(f"Archivo CSV generado en {output_dir}sales_data.csv")
