import os
from enum import Enum
from typing import Optional, Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException, Path, Query, Form, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# CONFIGURACIÓN DE BASE DE DATOS
# Recomendado: definir DB_URI como variable de entorno y no dejar la clave en el código.
DB_URI = os.getenv("DB_URI", "postgresql+psycopg2://postgres:9876s@localhost:54327/postgres")
engine = create_engine(DB_URI, pool_pre_ping=True)

app = FastAPI(
    title="API de Facturación de Energía y Estadísticas",
    description="API RESTful construida con FastAPI para liquidación de facturas y análisis de carga del sistema.",
    version="1.0.2"
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
# Consulta SQL para extraer todos los registros horarios del mes para el servicio
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
    # Sumatorias totales del mes
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

# Página principal: interfaz web (el HTML está al final de este archivo)
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    return HTML_PAGE

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
            detail=f"No se encontraron registros para el servicio ID {service_id} en el periodo {int(month)}/{int(year)}."
        )

    calc = process_invoice_calculation(df)
    return InvoiceDetailResponse(
        service_id=service_id,
        period=f"{int(month)}/{int(year)}",
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
            detail=f"No hay registros para el servicio {service_id} en {int(month)}/{int(year)}."
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
        period=f"{int(month)}/{int(year)}",
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


# INTERFAZ WEB (HTML)
# Esta página se sirve en "/" y consume los endpoints de arriba.

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Facturación de energía</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#EDF1F4; --ink:#13242F; --muted:#5B6E7A; --panel:#fff; --line:#D3DCE2;
  --cons:#1D6A96; --inj:#D98E04; --amber:#F4B400; --neg:#B3361F; --ok:#1F7A4D;
  --head:'Bricolage Grotesque','Segoe UI',system-ui,sans-serif;
  --body:'Public Sans','Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.5 var(--body)}
header{background:var(--ink);color:#fff;padding:28px 24px 0}
.wrap{max-width:1040px;margin:0 auto}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
h1{font:800 clamp(1.7rem,4vw,2.4rem)/1.1 var(--head);margin:0}
.sub{margin:6px 0 0;color:#B9C7D0;max-width:52ch}
.docs{color:var(--amber);font-weight:600;text-decoration:none;border-bottom:2px solid var(--amber);padding-bottom:1px}
nav{display:flex;gap:4px;margin-top:26px;overflow-x:auto}
nav button{background:none;border:0;color:#B9C7D0;font:600 .95rem var(--body);padding:12px 18px;cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap}
nav button[aria-selected=true]{color:#fff;border-bottom-color:var(--amber)}
main{padding:28px 24px 56px}
.grid{display:grid;grid-template-columns:300px 1fr;gap:24px;align-items:start}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:22px}
h2{font:600 1.15rem var(--head);margin:0 0 4px}
.hint{color:var(--muted);font-size:.9rem;margin:0 0 18px}
label{display:block;font-weight:500;font-size:.9rem;margin:14px 0 4px}
input,select{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:#fff;font:inherit;color:var(--ink)}
input:focus-visible,select:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid var(--amber);outline-offset:2px}
.go{margin-top:22px;width:100%;padding:12px;border:0;border-radius:6px;background:var(--ink);color:#fff;font:600 1rem var(--body);cursor:pointer}
.go:hover{background:#1F3A4A}
.go[disabled]{opacity:.6;cursor:wait}
.empty{color:var(--muted);padding:40px 8px;text-align:center}
.error{border:1px solid var(--neg);background:#FCEEEA;color:var(--neg);border-radius:6px;padding:12px 14px}
/* Recibo: el elemento memorable */
.receipt{background:#fff;border:1px solid var(--line);border-radius:4px;padding:26px 28px;position:relative;
  border-top:6px solid var(--amber);box-shadow:0 1px 0 var(--line)}
.receipt::after{content:"";position:absolute;left:0;right:0;bottom:-9px;height:9px;
  background:radial-gradient(circle at 7px -1px,var(--bg) 6px,transparent 7px) 0 0/14px 9px repeat-x}
.receipt h2{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.meta{color:var(--muted);font-size:.88rem;margin-bottom:14px}
.line{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px dashed var(--line)}
.line small{display:block;color:var(--muted);font-size:.82rem}
.num{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.neg{color:var(--ok)}
.total{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin-top:16px;padding-top:14px;border-top:2px solid var(--ink)}
.total strong{font:800 1.9rem var(--head);font-variant-numeric:tabular-nums}
.kwh{display:flex;gap:24px;margin-top:18px;color:var(--muted);font-size:.9rem;flex-wrap:wrap}
.kwh b{color:var(--ink)}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:560px){.stats{grid-template-columns:1fr}}
.stat{border:1px solid var(--line);border-top:5px solid var(--cons);border-radius:6px;padding:16px 18px;background:#fff}
.stat.inj{border-top-color:var(--inj)}
.stat h3{margin:0 0 8px;font:600 1rem var(--head)}
.stat .big{font:800 1.7rem var(--head);font-variant-numeric:tabular-nums}
.stat dl{margin:12px 0 0;display:grid;grid-template-columns:1fr auto;gap:4px 12px;font-size:.9rem}
.stat dt{color:var(--muted)} .stat dd{margin:0;text-align:right;font-variant-numeric:tabular-nums;font-weight:500}
.chartbox{position:relative;height:340px}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="top">
      <div>
        <h1>Facturación de energía</h1>
        <p class="sub">Calcula la factura de un servicio, revisa su consumo e inyección y mira la carga del sistema hora a hora.</p>
      </div>
      <a class="docs" href="/docs">Documentación de la API</a>
    </div>
    <nav role="tablist" aria-label="Secciones">
      <button role="tab" id="t-inv" aria-selected="true" data-tab="inv">Factura</button>
      <button role="tab" id="t-sta" aria-selected="false" data-tab="sta">Estadísticas del cliente</button>
      <button role="tab" id="t-load" aria-selected="false" data-tab="load">Carga del sistema</button>
    </nav>
  </div>
</header>

<main><div class="wrap">

<section id="inv" role="tabpanel" aria-labelledby="t-inv" class="grid">
  <form class="panel" id="f-inv">
    <h2>Calcular factura</h2>
    <p class="hint">Elige el servicio y el periodo a liquidar.</p>
    <label for="i-id">ID del servicio</label>
    <input id="i-id" type="number" min="1" value="2256" required>
    <label for="i-year">Año</label><select id="i-year"></select>
    <label for="i-month">Mes</label><select id="i-month"></select>
    <label for="i-concept">Qué quieres ver</label>
    <select id="i-concept">
      <option value="">Factura completa</option>
      <option value="EA">Solo EA · Energía activa</option>
      <option value="EC">Solo EC · Comercialización de excedentes</option>
      <option value="EE1">Solo EE1 · Excedentes tipo 1</option>
      <option value="EE2">Solo EE2 · Excedentes tipo 2</option>
      <option value="TOTAL">Solo el total neto</option>
    </select>
    <button class="go" type="submit">Calcular</button>
  </form>
  <div id="r-inv" aria-live="polite"><div class="panel empty">Elige un servicio y un periodo para calcular la factura.</div></div>
</section>

<section id="sta" role="tabpanel" aria-labelledby="t-sta" class="grid" hidden>
  <form class="panel" id="f-sta">
    <h2>Estadísticas del cliente</h2>
    <p class="hint">Sin año ni mes se usa todo el histórico.</p>
    <label for="s-id">ID del servicio</label>
    <input id="s-id" type="number" min="1" value="2256" required>
    <label for="s-year">Año (opcional)</label><select id="s-year"></select>
    <label for="s-month">Mes (opcional)</label><select id="s-month"></select>
    <button class="go" type="submit">Ver estadísticas</button>
  </form>
  <div id="r-sta" aria-live="polite"><div class="panel empty">Indica un servicio para ver su consumo e inyección.</div></div>
</section>

<section id="load" role="tabpanel" aria-labelledby="t-load" class="grid" hidden>
  <form class="panel" id="f-load">
    <h2>Carga del sistema</h2>
    <p class="hint">Consumo e inyección sumados de todos los servicios, por hora del día.</p>
    <label for="l-year">Año (opcional)</label><select id="l-year"></select>
    <label for="l-month">Mes (opcional)</label><select id="l-month"></select>
    <button class="go" type="submit">Ver carga</button>
  </form>
  <div id="r-load" aria-live="polite"><div class="panel empty">Pulsa «Ver carga» para dibujar la gráfica.</div></div>
</section>

</div></main>

<script>
const $ = (s, r = document) => r.querySelector(s);
const MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const cop = n => new Intl.NumberFormat('es-CO', {style:'currency', currency:'COP', maximumFractionDigits:2}).format(n);
const num = n => new Intl.NumberFormat('es-CO', {maximumFractionDigits:2}).format(n);
const kwh = n => num(n) + ' kWh';

// Selects de año y mes (los opcionales llevan una opción vacía)
function fill(prefix, optional, defYear, defMonth) {
  const y = $('#' + prefix + '-year'), m = $('#' + prefix + '-month');
  const blank = optional ? '<option value="">Todos</option>' : '';
  y.innerHTML = blank + Array.from({length:12}, (_, i) => 2026 - i).map(v => `<option value="${v}">${v}</option>`).join('');
  m.innerHTML = blank + MONTHS.map((n, i) => `<option value="${i+1}">${n}</option>`).join('');
  if (defYear) y.value = defYear;
  if (defMonth) m.value = defMonth;
}
fill('i', false, 2023, 9); fill('s', true); fill('l', true);

async function call(path, form) {
  const res = await fetch(path, form ? {method:'POST', body:new URLSearchParams(form)} : {});
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let d = data.detail;
    if (Array.isArray(d)) d = d.map(e => e.msg).join('. ');
    throw new Error(d || 'Error ' + res.status);
  }
  return data;
}

// Envía un formulario mostrando estado de carga y errores claros
function wire(id, target, run) {
  $('#' + id).addEventListener('submit', async e => {
    e.preventDefault();
    const btn = e.target.querySelector('.go'), label = btn.textContent;
    btn.disabled = true; btn.textContent = 'Calculando…';
    try { $(target).innerHTML = await run(); }
    catch (err) { $(target).innerHTML = `<div class="error" role="alert">${err.message}</div>`; }
    finally { btn.disabled = false; btn.textContent = label; }
  });
}

// ---- Factura ----
const ROWS = [
  ['ea_active_energy', 'EA', 'Energía activa consumida'],
  ['ec_excess_commercialization', 'EC', 'Comercialización de excedentes'],
  ['ee1_type1_excess', 'EE1', 'Excedentes tipo 1'],
  ['ee2_type2_excess', 'EE2', 'Excedentes tipo 2'],
];
wire('f-inv', '#r-inv', async () => {
  const id = $('#i-id').value, year = $('#i-year').value, month = $('#i-month').value, concept = $('#i-concept').value;
  const mName = MONTHS[month - 1];
  if (concept) {
    const d = await call('/calculate-concept', {service_id:id, year, month, concept});
    return `<div class="receipt"><h2>${d.concept === 'TOTAL' ? 'Total neto' : 'Concepto ' + d.concept}</h2>
      <div class="meta">Servicio ${d.service_id} · ${mName} ${year}</div>
      <div class="total"><span>Valor</span><strong>${cop(d.value)}</strong></div></div>`;
  }
  const d = await call('/calculate-invoice', {service_id:id, year, month});
  const lines = ROWS.map(([k, code, name]) =>
    `<div class="line"><span>${name}<small>${code}</small></span><span class="num ${d[k] < 0 ? 'neg' : ''}">${cop(d[k])}</span></div>`).join('');
  return `<div class="receipt"><h2>Factura de energía</h2>
    <div class="meta">Servicio ${d.service_id} · ${mName} ${year}</div>${lines}
    <div class="total"><span>Total neto</span><strong>${cop(d.total_net_invoice)}</strong></div>
    <div class="kwh"><span>Consumo <b>${kwh(d.total_consumption_kwh)}</b></span><span>Inyección <b>${kwh(d.total_injection_kwh)}</b></span></div></div>`;
});

// ---- Estadísticas ----
const qs = obj => { const p = new URLSearchParams(Object.entries(obj).filter(([, v]) => v)); return p.toString() ? '?' + p : ''; };
const block = (title, o, cls) => `<div class="stat ${cls}"><h3>${title}</h3><div class="big">${kwh(o.total_kwh)}</div>
  <dl><dt>Promedio por hora</dt><dd>${kwh(o.mean_hourly_kwh)}</dd><dt>Máximo por hora</dt><dd>${kwh(o.max_hourly_kwh)}</dd><dt>Mínimo por hora</dt><dd>${kwh(o.min_hourly_kwh)}</dd></dl></div>`;
wire('f-sta', '#r-sta', async () => {
  const id = $('#s-id').value;
  const d = await call(`/client-statistics/${id}` + qs({year:$('#s-year').value, month:$('#s-month').value}));
  return `<div class="meta">Servicio ${d.service_id} · ${d.period_filtered} · ${num(d.total_records)} registros</div>
    <div class="stats">${block('Consumo', d.consumption, '')}${block('Inyección', d.injection, 'inj')}</div>`;
});

// ---- Carga del sistema ----
let chart;
wire('f-load', '#r-load', async () => {
  if (!window.Chart) throw new Error('No se pudo cargar la librería de gráficas. Revisa tu conexión a internet.');
  const d = await call('/system-load' + qs({year:$('#l-year').value, month:$('#l-month').value}));
  setTimeout(() => {
    chart && chart.destroy();
    chart = new Chart($('#c-load'), {
      type:'bar',
      data:{labels:d.map(r => r.hour + ':00'), datasets:[
        {label:'Consumo', data:d.map(r => r.total_system_consumption_kwh), backgroundColor:'#1D6A96'},
        {label:'Inyección', data:d.map(r => r.total_system_injection_kwh), backgroundColor:'#D98E04'}]},
      options:{responsive:true, maintainAspectRatio:false,
        scales:{y:{title:{display:true, text:'kWh'}, beginAtZero:true}},
        plugins:{tooltip:{callbacks:{label:c => `${c.dataset.label}: ${kwh(c.parsed.y)}`,
          afterBody:i => `Servicios activos: ${d[i[0].dataIndex].active_services_count}`}}}}
    });
  }, 0);
  return `<div class="panel"><h2>Carga por hora del día</h2>
    <p class="hint">Pasa el cursor sobre una barra para ver el detalle.</p><div class="chartbox"><canvas id="c-load"></canvas></div></div>`;
});

// ---- Pestañas ----
document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('nav button').forEach(x => x.setAttribute('aria-selected', x === b));
  ['inv', 'sta', 'load'].forEach(t => $('#' + t).hidden = t !== b.dataset.tab);
}));
</script>
</body>
</html>
'''