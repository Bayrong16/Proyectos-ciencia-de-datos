# --- Ejemplo de ejecución ---


from funcion_conceptos_factura import calcular_factura_detallada


df_resultado = calcular_factura_detallada(id_servicio=2478, anio=2023, mes=9)
print(df_resultado)

#df_resultado.to_csv('resultado_factura.csv', index=False)
