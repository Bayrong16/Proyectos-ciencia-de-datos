

import pandas as pd     

df = pd.read_csv('resultado_consulta.csv')  # Leer el archivo CSV generado previamente



 # 3. Sumatorias totales del mes

total_consumo = df['consumo'].sum()
total_inyeccion = df['inyeccion'].sum()

# Obtenemos las tarifas CU y C (aplican para todo el servicio en el mes)
tarifa_cu = df['tarifa_cu'].iloc[0]
tarifa_c = df['tarifa_c'].iloc[0]

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

