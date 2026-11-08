# ⚡ API de Facturación de Energía y Análisis de Carga

Este proyecto es una solución integral que abarca desde el modelado y poblamiento de una base de datos relacional en **PostgreSQL**, pasando por la implementación de reglas de negocio para la liquidación tarifaria de energía, hasta la exposición de una **API RESTful** construida con **FastAPI**.

---
![Texto alternativo de la imagen](04. Data_base_project/images/postgreesql_esquema.png)

## 📌 Resumen del Flujo de Trabajo

El desarrollo se realizó de manera secuencial siguiendo las mejores prácticas de ingeniería de software y análisis de datos:

1. **Limpieza y Preparación de Datos (ETL/Data Cleaning):**
   - Análisis exploratorio previo sobre los archivos fuente `.csv`.
   - Normalización de formatos temporales, corrección de coordenadas geográficas y tratamiento de valores nulos o inconsistencias numéricas antes de la carga a base de datos.

2. **Modelado e Importación en PostgreSQL:**
   - Construcción del esquema relacional (6 tablas: `records`, `services`, `tariffs`, `consumption`, `injection`, `xm_data_hourly_per_agent`).
   - Definición de llaves primarias, foráneas e índices para optimizar las consultas de grandes volúmenes de series de tiempo.
   - Importación de los datos limpios desde los archivos `.csv` a las tablas correspondientes.

3. **Lógica de Negocio y Consultas Complejas en Python:**
   - Creación de scripts en Python utilizando **SQLAlchemy** y **Pandas** para ejecutar consultas optimizadas con `JOIN` y `LEFT JOIN`.
   - Implementación de la lógica de facturación de energía según la reglamentación aplicable:
     - **EA (Energía Activa):** Liquidación del consumo base.
     - **EC (Excedentes de Comercialización):** Liquidación de la inyección base.
     - **EE1 y EE2 (Excedentes Tipo 1 y Tipo 2):** Algoritmo acumulativo por hora cruzado con el precio de bolsa de energía (XM).

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

## ⚙️ Instrucciones de Despliegue Local

### 1. Requisitos Previos
- Python 3.9+
- Motor de base de datos PostgreSQL activo.

### 2. Instalación del Entorno
```bash
# Clonar el repositorio
git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
cd tu-repositorio

# Crear y activar entorno virtual
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
