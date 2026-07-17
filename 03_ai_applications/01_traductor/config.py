import os

from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables del archivo .env
load_dotenv()

# Leer la API Key
api_key = os.getenv("OPENROUTER_API_KEY")

# Crear el cliente
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

print("Configuración cargada correctamente")
print(f"API Key encontrada: {'Sí' if api_key else 'No'}")
