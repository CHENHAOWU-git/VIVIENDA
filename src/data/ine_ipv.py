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

# Códigos de serie del índice general (Índice, no variación) para Nacional y
# cada comunidad autónoma, en la vintage más reciente del INE (la serie viva
# a fecha de agosto de 2026; el INE ha rebasado el índice más de una vez, así
# que las series antiguas "Base 2007. <región>..." ya no se actualizan).
# Obtenidos filtrando `listar_series_ipv()` por nombre "<región>. General.
# Índice." Si el INE vuelve a rebasar el índice, hay que re-derivar este
# mapeo con esa misma función.
SERIES_INDICE_GENERAL = {
    "Nacional": "IPV1209",
    "Andalucía": "IPV1623",
    "Aragón": "IPV1638",
    "Asturias, Principado de": "IPV1653",
    "Balears, Illes": "IPV1668",
    "Canarias": "IPV1534",
    "Cantabria": "IPV1549",
    "Castilla - La Mancha": "IPV1579",
    "Castilla y León": "IPV1564",
    "Cataluña": "IPV1594",
    "Ceuta": "IPV1512",
    "Comunitat Valenciana": "IPV1392",
    "Extremadura": "IPV1407",
    "Galicia": "IPV1422",
    "Madrid, Comunidad de": "IPV1437",
    "Melilla": "IPV1517",
    "Murcia, Región de": "IPV1452",
    "Navarra, Comunidad Foral de": "IPV1467",
    "País Vasco": "IPV1482",
    "Rioja, La": "IPV1497",
}


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
    # La API del INE devuelve 404 si no se indica `nult`; sin límite explícito
    # pedimos un histórico amplio (la serie trimestral completa no llega a 100 puntos).
    params = {"nult": n_ultimos or 1000}
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


def obtener_evolucion_por_region(regiones: list[str] | None = None, n_ultimos: int | None = None) -> pd.DataFrame:
    """Descarga el índice general de precios de vivienda para Nacional +
    las comunidades autónomas indicadas (por defecto todas las de
    `SERIES_INDICE_GENERAL`) y las combina en un único DataFrame largo:
    columnas periodo, region, indice.
    """
    regiones = regiones or list(SERIES_INDICE_GENERAL.keys())
    frames = []
    for region in regiones:
        codigo = SERIES_INDICE_GENERAL[region]
        df = obtener_serie(codigo, n_ultimos=n_ultimos)
        df = df.rename(columns={"valor": "indice"})
        df["region"] = region
        frames.append(df)
    return pd.concat(frames, ignore_index=True).sort_values(["region", "periodo"]).reset_index(drop=True)
