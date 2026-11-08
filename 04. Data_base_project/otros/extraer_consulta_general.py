import pandas as pd
from sqlalchemy import create_engine

# 1. Tu conexión a PostgreSQL
DB_USER = "postgres"
DB_PASSWORD = "9876s" #colocar tu contraseña de conexión
DB_HOST = "localhost"
DB_PORT = "54327"  #colocar tu puerto de conexión
DB_NAME = "postgres" #colocar tu nombre de base de datos

db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

# 2. Parámetros de prueba
params = {
    "id_serv": 2256,      # Cambia por el ID de servicio a probar
    "anio": 2023,      # Año a evaluar
    "mes": 9           # Mes a evaluar
}

# 3Consulta SQL 
query = """
SELECT 
    r.record_timestamp,
    COALESCE(c.value, 0) AS consumo,
    COALESCE(i.value, 0) AS inyeccion,
    COALESCE(xm.value, 0) AS xm_value,
    t.cu AS tarifa_cu,
    t.c AS tarifa_c
FROM records r
JOIN services s ON r.id_service = s.id_service
JOIN tariffs t ON s.id_market = t.id_market 
                AND s.cdi = t.cdi 
                AND s.voltage_level = t.voltage_level
LEFT JOIN consumption c ON r.id_record = c.id_record
LEFT JOIN injection i ON r.id_record = i.id_record
LEFT JOIN xm_data_hourly_per_agent xm ON r.record_timestamp = xm.record_timestamp
WHERE r.id_service = %(id_serv)s
    AND EXTRACT(YEAR FROM r.record_timestamp) = %(anio)s
    AND EXTRACT(MONTH FROM r.record_timestamp) = %(mes)s
ORDER BY r.record_timestamp;
"""

with engine.connect() as connection:
    df = pd.read_sql(query, con=engine, params=params)
# 5. Mostrar resultados
print(f"✅ ¡Consulta exitosa! Se cargaron {len(df)} registros.")
print(df.head())

df.to_csv('resultado_consulta.csv', index=False) #guardar el resultado en un archivo CSV para su posterior análisis
