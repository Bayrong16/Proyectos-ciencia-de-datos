# 🚀 Guía Rápida de Ejecución

Sigue estos pasos resumidos para poner a correr el proyecto en tu entorno local:

---

### 1. Preparar la Base de Datos (PostgreSQL)
1. Asegúrate de tener instalado **PostgreSQL** y **pgAdmin**.
2. Abre pgAdmin y **crea una base de datos nueva** (ej. `bd_facturacion`).
3. Haz clic derecho sobre la base de datos creada, selecciona **Restore...** (Restaurar) e importa el archivo `esquema_base_datos.sql` incluido en el repositorio para cargar las tablas y los datos.

---

### 2. Configurar el Entorno de Python
Abre una terminal (PowerShell o CMD) en la raíz del proyecto dentro de Visual Studio Code:

```bash
# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias requeridas
pip install -r requirements.txt
```

---

### 3. Probar Funciones Locales (Opcional)
Puedes verificar el funcionamiento de las consultas y la lógica de negocio ejecutando los scripts de prueba:
```bash
python funcion_conceptos_factura.py
python pruebas_factura.py
```

---

### 4. Iniciar el Servidor de la API (FastAPI)
En la terminal de PowerShell dentro de VS Code, ejecuta el servidor ASGI **Uvicorn** en el puerto 8000:

```bash
python -m uvicorn main:app --reload --port 8000
```

---

### 5. Interactuar con la API
Una vez que la terminal indique que el servidor está corriendo en `http://127.0.0.1:8000`:

1. Abre tu navegador web y entra a la interfaz interactiva:
   👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
2. Desde la interfaz de **Swagger UI** podrás probar interactivamente los distintos endpoints:
   - **`POST`**: Calcular factura completa (`/calculate-invoice`) o conceptos individuales (`/calculate-concept`).
   - **`GET`**: Consultar estadísticas por cliente (`/client-statistics/{service_id}`) y perfil de carga del sistema (`/system-load`).