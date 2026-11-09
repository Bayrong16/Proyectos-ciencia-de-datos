# ⚡ API de Facturación de Energía y Análisis de Carga

Este proyecto es una solución integral que abarca desde el modelado y poblamiento de una base de datos relacional en **PostgreSQL**, pasando por la implementación de reglas de negocio para la liquidación tarifaria de energía, hasta la exposición de una **API RESTful** construida con **FastAPI**.

 ![FacturaAPI](./images/factura.png)
---

# 📌 Resumen del Flujo de Trabajo

El desarrollo se realizó de manera secuencial siguiendo las mejores prácticas de ingeniería de software y análisis de datos:

1. **Limpieza y Preparación de Datos (ETL/Data Cleaning):**
   - Análisis exploratorio previo sobre los archivos fuente `.csv`.
   - Normalización de formatos temporales, corrección de coordenadas geográficas y tratamiento de valores nulos o inconsistencias numéricas antes de la carga a base de datos.

2. **Modelado e Importación en PostgreSQL:**
   - Construcción del esquema relacional (6 tablas: `records`, `services`, `tariffs`, `consumption`, `injection`, `xm_data_hourly_per_agent`).
   - Definición de llaves primarias, foráneas e índices para optimizar las consultas de grandes volúmenes de series de tiempo.
   - Importación de los datos limpios desde los archivos `.csv` a las tablas correspondientes.
   - -la base de datos creada está disponible para su uso; consultar: base_datos_energia.sql

                 *Esquema de la base de datos*
   ![esquema SQL implementado](./images/postgreesql_esquema.png)

3. **Lógica de Negocio y Consultas Complejas en Python:**
   - Creación de scripts en Python utilizando **SQLAlchemy** y **Pandas** para ejecutar consultas optimizadas con `JOIN` y `LEFT JOIN`.
   - Implementación de la lógica de facturación de energía según la reglamentación aplicable:
     - **EA (Energía Activa):** Liquidación del consumo base.
     - **EC (Excedentes de Comercialización):** Liquidación de la inyección base.
     - **EE1 y EE2 (Excedentes Tipo 1 y Tipo 2):** Algoritmo acumulativo por hora cruzado con el precio de bolsa de energía (XM).
    
La siguiente figura muestra de forma intuitiva cómo se relaciona la consulta principal SQL con el resultado obtenido; se toma como ejemplo las dos primeras filas del resultado.
![esquema consultao](./images/consulta.png)

4. **Desarrollo y Exposición de la API con FastAPI:**
   - Construcción de endpoints `POST` y `GET` para consultar facturas, evaluar conceptos específicos, obtener métricas por cliente y consultar la curva de carga horaria del sistema.
   - Integración de validaciones robustas con **Pydantic** y listas desplegables `Enum` para facilitar la interacción desde Swagger UI.

---

## 🚀 Arquitectura de Endpoints (API)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/calculate-invoice` | Liquidación completa detallada de la factura (EA, EC, EE1, EE2 y Total Neto). |
| `POST` | `/calculate-concept` | Liquidación independiente de un concepto tarifario específico (`EA`, `EC`, `EE1`, `EE2` o `TOTAL`). |
| `GET` | `/client-statistics/{service_id}` | Métricas y estadísticas de consumo e inyección filtrables por año y mes. |
| `GET` | `/system-load` | Perfil horaria de carga del sistema (franja de 0 a 23 horas) agregada a nivel global. |

---

# 🚀 Guía Rápida de Ejecución

Sigue estos pasos resumidos para poner a correr el proyecto en tu entorno local:

---

### 1. Preparar la Base de Datos (PostgreSQL)
1. Asegúrate de tener instalado **PostgreSQL** (recomendado v.16) y **pgAdmin**.
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
Puedes verificar el funcionamiento de las consultas y la lógica de negocio ejecutando el script principal:
```bash
- python funcion_conceptos_factura.py , el cual contiene todo el código y lógica de los conceptos de la factura;
al final se encuentran algunas pruebas de errores realizadas.

En la carpeta de "otros" encuentras:
-prueba_factura.py  para probar en otro script el funcionamiento del principal;
-archivo extraer_consulta_general.py sirve para obtener en un .csv la consulta principal útil para su posterior análisis y verificación;
-archivos .csv de consulta y resultado,  obtenidos en pruebas locales.
-main1.py, es la versión inicial de la APIrest, con la interfaz sencilla.

```

---

### 4. Iniciar el Servidor de la API (FastAPI)
Asegurate de ejecutar el archivo main.py. el cual contiene todo el código y lógica de la API implementada.
Luego en la terminal de PowerShell(se recomienda en un terminal nuevo)dentro de VS Code, ejecuta el servidor ASGI **Uvicorn** en el puerto 8000:

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
  
3. si abres el navegador en **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**, habrá un dashboard web que consume la API,
es decir una interfaz con la que se puede interactuar de forma amigable.
