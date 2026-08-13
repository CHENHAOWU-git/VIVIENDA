"""Cliente para el Índice de Precios de Vivienda (IPV) del INE.

Fuente oficial y de acceso libre (sin registro): API Tempus3 del INE.
Útil para contrastar la evolución de tus datos scrapeados con la referencia
estadística oficial (agregada por trimestre y comunidad autónoma/provincia,
no por vivienda individual).

Documentación general: https://www.ine.es/dyngs/DAB/index.htm?cid=1100
Catálogo de datos abiertos: https://datos.gob.es/es/catalogo/ea0042823-indice-de-precios-de-la-vivienda-ipv
"""
from __future__ import annotations

import pandas as pd
import requests

BASE_URL = "https://servicios.ine.es/wstempus/js/ES"
OPERACION_IPV = "IPV"  # código de la operación estadística "Índice de Precios de Vivienda"


def listar_series_ipv(page: int = 1) -> list[dict]:
    """Lista las series disponibles bajo la operación IPV (para localizar el
    código de la serie concreta que te interese: general, vivienda nueva,
    segunda mano, por comunidad autónoma, etc.)."""
    url = f"{BASE_URL}/SERIES_OPERACION/{OPERACION_IPV}"
    response = requests.get(url, params={"page": page}, timeout=15)
    response.raise_for_status()
    return response.json()


def obtener_serie(codigo_serie: str, n_ultimos: int | None = None) -> pd.DataFrame:
    """Descarga los datos de una serie del IPV dado su código (obtenido con
    `listar_series_ipv`).

    Devuelve un DataFrame con columnas: periodo, valor.
    """
    url = f"{BASE_URL}/DATOS_SERIE/{codigo_serie}"
    params = {"nult": n_ultimos} if n_ultimos else {}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    datos = payload.get("Data", payload) if isinstance(payload, dict) else payload
    df = pd.DataFrame(datos)
    if "Fecha" in df.columns:
        df["periodo"] = pd.to_datetime(df["Fecha"], unit="ms")
    if "Valor" in df.columns:
        df = df.rename(columns={"Valor": "valor"})
    return df[["periodo", "valor"]] if {"periodo", "valor"}.issubset(df.columns) else df
