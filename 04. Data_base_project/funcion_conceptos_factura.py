import pandas as pd
#import psycopg2
from sqlalchemy import create_engine

def calcular_factura_detallada(id_servicio, anio, mes):
    """
    Calcula EA, EC, EE1 y EE2 acorde a reglas establecidas
    para un servicio y mes específico, utilizando SQLAlchemy.
    """
    # 1. Configuración de la conexión con SQLAlchemy
    # Reemplaza 'postgresql+psycopg2://postgres:password@localhost:54327/postgres'
    db_uri = 'postgresql+psycopg2://postgres:9876s@localhost:54327/postgres'

    # Intenta conectar a la BD; si falla (por URL incorrecta o credenciales), 
    # captura el error y devuelve un mensaje explicativo sin romper el programa
    try:
        engine = create_engine(db_uri)
    except Exception as e:
        return f"Error al crear el motor de conexión: {e}"

    
    # 2. Consulta SQL para extraer todos los registros horarios del mes para el servicio
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

    try:
        # Usamos pandas con el engine de SQLAlchemy (sin generar advertencias)
        df = pd.read_sql(query, con=engine, params={"id_serv": id_servicio, "anio": anio, "mes": mes})

        if df.empty:
            return f"No hay datos para el servicio {id_servicio} en el periodo {mes}/{anio}."

        # 3. Sumatorias totales del mes
        total_consumo = df['consumo'].sum()
        total_inyeccion = df['inyeccion'].sum()
        
        # Obtenemos las tarifas CU y C (aplican para todo el servicio en el mes)
        tarifa_cu = df['tarifa_cu'].iloc[0]
        tarifa_c = df['tarifa_c'].iloc[0]

        # CONCEPTOS PRINCIPALES (Acorde a las Reglas)
      
        # --- A. Energía Activa (EA) ---
        EA = total_consumo * tarifa_cu

        # --- B. Comercialización de Excedentes (EC) ---
        EC = total_inyeccion * tarifa_c

       # --- C. Excedentes de Energía tipo 1 (EE1) ---
        cantidad_ee1 = min(total_inyeccion, total_consumo)
        EE1 = cantidad_ee1 * (-tarifa_cu)  # Tarifa CU negativa

        # --- D. Excedentes de Energía tipo 2 (EE2) con lógica acumulativa ---
        EE2 = 0
        if total_inyeccion > total_consumo:
            # 1. Calculamos la inyección acumulada hora a hora en el mes
            df['inyeccion_acumulada'] = df['inyeccion'].cumsum()
            
            # 2. Calculamos el exceso acumulado superando el total del consumo
            # Esto nos dice cuántos kWh acumulados van para EE2 hasta esa hora
            df['exceso_acumulado'] = (df['inyeccion_acumulada'] - total_consumo).apply(lambda x: max(0, x))
            
            # 3. Restamos el exceso de la hora anterior para saber exactamente cuántos kWh 
            # de EE2 se generaron en ESTA hora específica
            df['exceso_hora_ee2'] = df['exceso_acumulado'] - df['exceso_acumulado'].shift(1).fillna(0)
            
            # 4. Multiplicamos esos kWh de la hora por el valor de XM de esa hora y sumamos todo
            df['ee2_parcial'] = df['exceso_hora_ee2'] * df['xm_value']
            EE2 = df['ee2_parcial'].sum()

        #Calculo del valor neto de la factura
        Total_factura_neto = EA + EC + EE1 + EE2 

        # Resultado final estructurado
        resultado = {
            "Servicio ID": id_servicio,
            "Periodo": f"{mes}/{anio}",
            "Total Consumo [kWh]": round(total_consumo, 2),
            "Total Inyección [kWh]": round(total_inyeccion, 2),
            "EA (Energía Activa) [$]": round(EA, 2),
            "EC (Comercialización Excedentes) [$]": round(EC, 2),
            "EE1 (Excedentes Tipo 1) [$]": round(EE1, 2),
            "EE2 (Excedentes Tipo 2) [$]": round(EE2, 2),
            "Total Factura Neto [$]": round(Total_factura_neto, 2)
        }

        return pd.DataFrame([resultado]).T  #.T para mostrar el resultado en formato vertical (columnas como índice)

    except Exception as e:
        return f"Error ejecutando la consulta o el cálculo: {e}"

if __name__ == "__main__":
    print("--- PROBANDO MANEJO DE ERRORES ---")
    
    # 1. Prueba con un ID de servicio que NO exista en la base de datos
    print("\nProbando servicio inexistente")
    calcular_factura_detallada(id_servicio=1234, anio=2023, mes=9)

    # 2. Prueba con un mes inválido (ej: mes 13)
    print("\nProbando mes inválido (Mes 13):")
    try:
        calcular_factura_detallada(id_servicio=2256, anio=2023, mes=13)
    except ValueError as ve:
        print(f"Validación exitosa capturada: {ve}")