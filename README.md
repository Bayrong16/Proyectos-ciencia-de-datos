Análisis Exploratorio de Datos (EDA) de Producción de Energía, Patrones y Anomalías de un Autogenerador
realizado por: Bayron A. Guamá
resumen:
1. Limpieza de datos
2. Análisis y Visualización
3. Conclusiones
Fuente de datos: anonimo


Conclusiones Generales del Análisis de Producción de Energía:

Datos Completos y Limpios: La base de datos inicial está bien estructurada y completa, sin valores faltantes, y se ha limpiado adecuadamente para facilitar el análisis, incluyendo la estandarización de los nombres de las columnas y la correcta conversión de la columna de fecha.

Distribución Temporal de los Datos: Los datos cubren un período significativo, permitiendo un análisis de tendencias anuales y mensuales en la producción de energía activa.

Patrón Mensual de Producción: Se observa una clara tendencia mensual en la producción de energía activa promedio a lo largo de 2023. Hubo un valle notable en abril, un aumento gradual hasta un pico en noviembre, y un descenso en diciembre. Este patrón sugiere una fuerte influencia de factores estacionales, probablemente relacionados con los patrones de nubosidad y precipitación en un clima tropical como el de Colombia.

Variabilidad Diaria y Días Anómalos: El análisis de los boxplots y gráficos de línea diarios reveló una variabilidad significativa en la producción de energía de un día a otro dentro de cada mes. Crucialmente, se identificaron días específicos en cada mes con producciones de energía atípicamente bajas. Causas Probables de la Baja Producción: La coincidencia de algunos días de baja producción con domingos y festivos sugiere que la reducción en la demanda interna de la instalación influye en la operación del autogenerador. Otros días de baja producción no relacionados con el calendario indican la probable influencia de condiciones climáticas desfavorables (alta nubosidad, lluvia) o posibles eventos operativos como mantenimientos o fallas parciales del sistema.

Estimación de la Capacidad Instalada: Basándonos en el valor máximo de energía activa registrado en un intervalo horario (aproximadamente 2190.75 kWh), se estima que la potencia instalada del autogenerador es de al menos 2190.75 kW. Esto indica una instalación de capacidad considerable, coherente con un autogenerador a gran escala.

Relevancia para la Planificación: El análisis detallado del comportamiento de producción de este autogenerador, incluyendo sus patrones mensuales, variabilidad diaria y la ocurrencia de días de baja producción, proporciona una base de referencia valiosa para quienes consideren instalar un autogenerador de tamaño similar. No obstante, se subraya la importancia crítica de analizar las condiciones específicas de la ubicación de cualquier nueva instalación, ya que los factores climáticos locales tienen un impacto directo en la producción.
el siguiente paso será analizar cuánto fue el ahorro en la factura de energía por autogeneracion.

--> otro posible analisis: determinar el tamaño de otro parque solar, con distinta capacidad y simular la energía generada. (Machine learning
