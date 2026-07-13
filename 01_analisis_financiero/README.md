# 📊 Análisis Financiero y Riesgo de Crédito

## 📝 1. Análisis de Datos Financieros

En este proyecto se realizó un análisis exhaustivo de datos financieros utilizando **Python** y su ecosistema de librerías especializadas, cubriendo desde la preparación inicial de los datos hasta su puesta a punto para el modelado predictivo.

### 🔍 Análisis Exploratorio de Datos (EDA) y Preprocesamiento
* **Tratamiento de Datos Faltantes:** Se llevó a cabo un proceso riguroso de limpieza mediante la imputación de datos utilizando la **media** para variables numéricas y la **moda** para las categóricas.
* **Agrupaciones y Visualización:** A través de operaciones de agregación (`groupby`), se examinaron los patrones de comportamiento de las variables clave del negocio.

### 💡 Hallazgo Clave (Insight)
Durante la fase de exploración se identificó una anomalía crítica: **las ganancias promedio del segmento "Empresa" resultaron ser negativas**, a pesar de que sus ventas promedio se posicionaban como las segundas más importantes del negocio, solo por detrás del segmento de "Pequeños Negocios". 

A continuación se presenta la visualización que justifica y demuestra esta conclusión:

![Análisis de Ganancias y Ventas por Segmento](./images/ganancia_ventas.png)

### ⚙️ Ingeniería de Características y Preparación para Machine Learning
Para garantizar la calidad de los datos antes de ser transferidos a un modelo predictivo de Machine Learning, se aplicaron las siguientes técnicas de ingeniería de características:
* **Codificación de Variables:** Se transformaron las variables categóricas mediante la técnica de *One-Hot Encoding*.
* **Control de Multicolinealidad:** Se evaluó el Factor de Inflación de la Varianza (**VIF**) para identificar y remover características altamente correlacionadas, asegurando la estabilidad de un futuro modelo.

Aquí se puede observar la estructura final de relaciones del conjunto de datos procesado (pasamos de 10 carácteristicas a 6):

![Matriz de Correlación Final](./images/matriz_correlacion.png)

---

## 🛡️ 2. Análisis de Datos de Riesgo Crediticio

> 🚧 **Proyecto en Desarrollo**
> Actualmente me encuentro trabajando en esta sección. Aquí se incluirá el análisis detallado, la metodología de evaluación del riesgo de crédito y los modelos de regresión aplicados.

---
🔗 *[Volver al menú principal](../README.md)*
