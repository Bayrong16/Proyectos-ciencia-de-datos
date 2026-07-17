from fastapi import FastAPI

from app.routes import router

# Crear la aplicación FastAPI
app = FastAPI(
    title="Translator API",
    version="1.0.0",
    description="API para traducir texto usando OpenRouter"
)

# Registrar todas las rutas definidas en routes.py
app.include_router(router)