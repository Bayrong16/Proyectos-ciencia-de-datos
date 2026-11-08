from fastapi import FastAPI, HTTPException, Path, Query, Form, status # <--- Importar Form
from enum import Enum
from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# CONFIGURACIÓN DE BASE DE DATOS

DB_URI = 'postgresql+psycopg2://postgres:9876s@localhost:54327/postgres'
engine = create_engine(DB_URI, pool_pre_ping=True)

app = FastAPI(
    title="API de Facturación de Energía y Estadísticas",
    description="API RESTful construida con FastAPI para liquidación de facturas y análisis de carga del sistema.",
    version="1.0.1"
)

# DEFINICIÓN DE ENUMS PARA LISTAS DESPLEGABLES EN SWAGGER

class YearEnum(int, Enum):
    y2015 = 2015
    y2016 = 2016
    y2017 = 2017
    y2018 = 2018
    y2019 = 2019
    y2020 = 2020
    y2021 = 2021
    y2022 = 2022
    y2023 = 2023
    y2024 = 2024
    y2025 = 2025
    y2026 = 2026

class MonthEnum(int, Enum):
    Enero = 1
    Febrero = 2
    Marzo = 3
    Abril = 4
    Mayo = 5
    Junio = 6
    Julio = 7
    Agosto = 8
    Septiembre = 9
    Octubre = 10
    Noviembre = 11
    Diciembre = 12

class ConceptEnum(str, Enum):
    EA = "EA"
    EC = "EC"
    EE1 = "EE1"
    EE2 = "EE2"
    TOTAL = "TOTAL"

# SCHEMAS DE PYDANTIC (Modelos de Entrada y Salida)

class CalculateInvoiceRequest(BaseModel):
    service_id: int = Field(..., gt=0, description="ID del servicio (entero positivo)", example=2256)
    year: YearEnum = Field(..., description="Selecciona el año del periodo", example=YearEnum.y2023)
    month: MonthEnum = Field(..., description="Selecciona el mes del periodo", example=MonthEnum.Septiembre)

class InvoiceDetailResponse(BaseModel):
    service_id: int
    period: str
    total_consumption_kwh: float
    total_injection_kwh: float
    ea_active_energy: float
    ec_excess_commercialization: float
    ee1_type1_excess: float
    ee2_type2_excess: float
    total_net_invoice: float

class ConceptCalculationRequest(BaseModel):
    service_id: int = Field(..., gt=0, example=2256)
    year: YearEnum = Field(..., description="Selecciona el año", example=YearEnum.y2023)
    month: MonthEnum = Field(..., description="Selecciona el mes", example=MonthEnum.Septiembre)
    concept: ConceptEnum = Field(..., description="Selecciona el concepto a calcular", example=ConceptEnum.EE2)

class ConceptCalculationResponse(BaseModel):
    service_id: int
    period: str
    concept: str
    value: float
    unit: str = "COP"

class ClientStatisticsResponse(BaseModel):
    service_id: int
    period_filtered: Optional[str]
    total_records: int
    consumption: Dict[str, float]
    injection: Dict[str, float]

class HourlyLoadItem(BaseModel):
    hour: int
    total_system_consumption_kwh: float
    total_system_injection_kwh: float
    active_services_count: int

# LÓGICA DE NEGOCIO Y EXTRACCIÓN (SERVICES)
#Consulta SQL para extraer todos los registros horarios del mes para el servicio
def fetch_service_records(service_id: int, year: int, month: int) -> pd.DataFrame:
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
        df = pd.read_sql(query, con=engine, params={"id_serv": service_id, "anio": year, "mes": month})
        return df
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la base de datos PostgreSQL: {str(db_err)}"
        )

def process_invoice_calculation(df: pd.DataFrame) -> Dict[str, float]:
    #Sumatorias totales del mes
    total_consumo = float(df['consumo'].sum())
    total_inyeccion = float(df['inyeccion'].sum())
    tarifa_cu = float(df['tarifa_cu'].iloc[0])
    tarifa_c = float(df['tarifa_c'].iloc[0])

    # CONCEPTOS PRINCIPALES (Acorde a las Reglas)
    EA = total_consumo * tarifa_cu
    EC = total_inyeccion * tarifa_c
    cantidad_ee1 = min(total_inyeccion, total_consumo)
    EE1 = cantidad_ee1 * (-tarifa_cu)

    EE2 = 0.0
    if total_inyeccion > total_consumo:
        df['inyeccion_acumulada'] = df['inyeccion'].cumsum()
        df['exceso_acumulado'] = (df['inyeccion_acumulada'] - total_consumo).apply(lambda x: max(0, x))
        df['exceso_hora_ee2'] = df['exceso_acumulado'] - df['exceso_acumulado'].shift(1).fillna(0)
        df['ee2_parcial'] = df['exceso_hora_ee2'] * df['xm_value']
        EE2 = float(df['ee2_parcial'].sum())

    total_neto = EA + EC + EE1 + EE2

    return {
        "total_consumo": round(total_consumo, 2),
        "total_inyeccion": round(total_inyeccion, 2),
        "EA": round(EA, 2),
        "EC": round(EC, 2),
        "EE1": round(EE1, 2),
        "EE2": round(EE2, 2),
        "total_neto": round(total_neto, 2)
    }

# ENDPOINTS DE LA API

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Facturación de Energía y Estadísticas ⚡"}

# 1. Endpoint /calculate-invoice con Formularios (genera desplegables en Swagger)
@app.post(
    "/calculate-invoice",
    response_model=InvoiceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula la factura completa para un servicio y periodo determinado."
)
def calculate_invoice(
    service_id: int = Form(..., description="ID del servicio (entero positivo)", example=2256),
    year: YearEnum = Form(..., description="Selecciona el año del periodo"),
    month: MonthEnum = Form(..., description="Selecciona el mes del periodo")
):
    df = fetch_service_records(service_id, int(year), int(month))
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron registros para el servicio ID {service_id} en el periodo {month}/{year}."
        )

    calc = process_invoice_calculation(df)
    return InvoiceDetailResponse(
        service_id=service_id,
        period=f"{month}/{year}",
        total_consumption_kwh=calc["total_consumo"],
        total_injection_kwh=calc["total_inyeccion"],
        ea_active_energy=calc["EA"],
        ec_excess_commercialization=calc["EC"],
        ee1_type1_excess=calc["EE1"],
        ee2_type2_excess=calc["EE2"],
        total_net_invoice=calc["total_neto"]
    )


# 2. Endpoint /calculate-concept con Formularios
@app.post(
    "/calculate-concept",
    response_model=ConceptCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula de forma independiente un concepto específico de la factura."
)
def calculate_concept(
    service_id: int = Form(..., description="ID del servicio", example=2256),
    year: YearEnum = Form(..., description="Selecciona el año"),
    month: MonthEnum = Form(..., description="Selecciona el mes"),
    concept: ConceptEnum = Form(..., description="Selecciona el concepto a calcular")
):
    df = fetch_service_records(service_id, int(year), int(month))
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay registros para el servicio {service_id} en {month}/{year}."
        )

    calc = process_invoice_calculation(df)
    
    mapping_values = {
        "EA": calc["EA"],
        "EC": calc["EC"],
        "EE1": calc["EE1"],
        "EE2": calc["EE2"],
        "TOTAL": calc["total_neto"]
    }

    return ConceptCalculationResponse(
        service_id=service_id,
        period=f"{month}/{year}",
        concept=concept.value,
        value=mapping_values[concept.value]
    )

# 3. GET /client-statistics/{service_id}
@app.get(
    "/client-statistics/{service_id}",
    response_model=ClientStatisticsResponse,
    summary="Proporciona estadísticas completas de consumo e inyección para un servicio."
)
def get_client_statistics(
    service_id: int = Path(..., gt=0, description="ID del servicio"),
    year: Optional[int] = Query(None, ge=2015, le=2026, description="Filtrar por año opcional"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mes opcional")
):
    where_clauses = ["r.id_service = %(service_id)s"]
    params = {"service_id": service_id}

    if year:
        where_clauses.append("EXTRACT(YEAR FROM r.record_timestamp) = %(year)s")
        params["year"] = year
    if month:
        where_clauses.append("EXTRACT(MONTH FROM r.record_timestamp) = %(month)s")
        params["month"] = month

    where_str = " AND ".join(where_clauses)

    query = f"""
    SELECT 
        COALESCE(c.value, 0) AS consumo,
        COALESCE(i.value, 0) AS inyeccion
    FROM records r
    LEFT JOIN consumption c ON r.id_record = c.id_record
    LEFT JOIN injection i ON r.id_record = i.id_record
    WHERE {where_str};
    """

    try:
        df = pd.read_sql(query, con=engine, params=params)
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail=f"Error en consulta de estadísticas: {str(db_err)}")

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron datos estadísticos para el servicio ID {service_id}."
        )

    period_str = f"{month}/{year}" if (year and month) else (str(year) if year else "Histórico Completo")

    return ClientStatisticsResponse(
        service_id=service_id,
        period_filtered=period_str,
        total_records=len(df),
        consumption={
            "total_kwh": round(float(df['consumo'].sum()), 2),
            "mean_hourly_kwh": round(float(df['consumo'].mean()), 2),
            "max_hourly_kwh": round(float(df['consumo'].max()), 2),
            "min_hourly_kwh": round(float(df['consumo'].min()), 2)
        },
        injection={
            "total_kwh": round(float(df['inyeccion'].sum()), 2),
            "mean_hourly_kwh": round(float(df['inyeccion'].mean()), 2),
            "max_hourly_kwh": round(float(df['inyeccion'].max()), 2),
            "min_hourly_kwh": round(float(df['inyeccion'].min()), 2)
        }
    )

# 4. GET /system-load
@app.get(
    "/system-load",
    response_model=List[HourlyLoadItem],
    summary="Muestra la carga agregada del sistema por hora del día (0-23) basada en los datos globales."
)
def get_system_load(
    year: Optional[int] = Query(None, ge=2015, le=2026, description="Filtrar por año"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mes")
):
    where_clauses = []
    params = {}

    if year:
        where_clauses.append("EXTRACT(YEAR FROM r.record_timestamp) = %(year)s")
        params["year"] = year
    if month:
        where_clauses.append("EXTRACT(MONTH FROM r.record_timestamp) = %(month)s")
        params["month"] = month

    where_str = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
    SELECT 
        EXTRACT(HOUR FROM r.record_timestamp)::INT AS hora,
        SUM(COALESCE(c.value, 0)) AS total_consumo,
        SUM(COALESCE(i.value, 0)) AS total_inyeccion,
        COUNT(DISTINCT r.id_service) AS servicios_activos
    FROM records r
    LEFT JOIN consumption c ON r.id_record = c.id_record
    LEFT JOIN injection i ON r.id_record = i.id_record
    {where_str}
    GROUP BY EXTRACT(HOUR FROM r.record_timestamp)
    ORDER BY hora;
    """

    try:
        df = pd.read_sql(query, con=engine, params=params)
    except SQLAlchemyError as db_err:
        raise HTTPException(status_code=500, detail=f"Error al calcular la carga del sistema: {str(db_err)}")

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se registraron datos de carga para el filtro especificado."
        )

    load_items = []
    for _, row in df.iterrows():
        load_items.append(
            HourlyLoadItem(
                hour=int(row['hora']),
                total_system_consumption_kwh=round(float(row['total_consumo']), 2),
                total_system_injection_kwh=round(float(row['total_inyeccion']), 2),
                active_services_count=int(row['servicios_activos'])
            )
        )

    return load_items