# 🌐 Translator API with FastAPI & OpenRouter

API REST desarrollada en **Python** utilizando **FastAPI** y **OpenRouter** para traducir texto del inglés al español mediante un modelo de lenguaje (LLM).

El proyecto fue diseñado siguiendo una arquitectura modular, separando la configuración, los modelos de datos, la lógica de negocio y las rutas de la API, facilitando su mantenimiento, escalabilidad y reutilización.

## Características

- Traducción de texto mediante modelos de IA.
- API REST desarrollada con FastAPI.
- Documentación automática con Swagger (`/docs`).
- Validación de datos con Pydantic.
- Configuración mediante variables de entorno (`.env`).
- Arquitectura modular siguiendo buenas prácticas de desarrollo.

## Tecnologías

- Python
- FastAPI
- Pydantic
- OpenAI SDK
- OpenRouter
- Uvicorn

## Estructura del proyecto

```text
app/
│
├── config.py      # Configuración y conexión con OpenRouter
├── main.py        # Punto de entrada de la aplicación
├── models.py      # Modelos de entrada y salida
├── routes.py      # Endpoints de la API
├── services.py    # Lógica de traducción
└── __init__.py
```

## Endpoint disponible

| Método | Endpoint | Descripción |
|---------|----------|-------------|
| POST | `/translate` | Traduce texto del inglés al español. |

## Ejemplo de solicitud

```json
{
    "input_str": "Good morning"
}
```

## Ejemplo de respuesta

```json
{
    "translated_text": "Buenos días"
}
```

## Próximas mejoras

- Traducción entre múltiples idiomas.
- Resumen automático de textos.
- Análisis de sentimientos.
- Extracción de palabras clave.
- Manejo avanzado de errores.
- Pruebas automatizadas.
- Contenerización con Docker.
- Despliegue en la nube.
