"""Datasets abiertos de vivienda, sin necesidad de credenciales ni cuenta.

Reemplazo/complemento de la API de Idealista mientras no se dispone de
credenciales: fuentes ya publicadas en Zenodo (acceso libre, descarga
directa de CSV) que incluyen precio, m2, habitaciones, baños y localización
a nivel de vivienda individual.

Fuentes:
- Fotocasa (alquiler, Madrid + Alicante, por barrio): Rezzak Liman, O. (2021).
  https://doi.org/10.5281/zenodo.5599647 (CC-BY 4.0)
- properties_Spain.csv (venta/alquiler, cobertura nacional):
  https://doi.org/10.5281/zenodo.14028180 (MIT)
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path("data/raw")

FOTOCASA_URL = "https://zenodo.org/record/5599647/files/Fotocasa.csv?download=1"
PROPERTIES_SPAIN_URL = "https://zenodo.org/records/14028180/files/properties_Spain.csv?download=1"

COLUMNAS_ESTANDAR = [
    "fecha_publicacion", "precio", "superficie_m2", "habitaciones",
    "banos", "ciudad", "zona", "direccion", "tipo_inmueble", "url",
]


def _descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    destino.write_bytes(response.content)
    return destino


def cargar_fotocasa_madrid_alicante() -> pd.DataFrame:
    """Descarga y normaliza el dataset de alquiler de Fotocasa (Madrid + Alicante).

    Nota sobre calidad de datos: la columna `price` del CSV original mezcla
    dos formatos (algunas filas en miles de euros con coma decimal exportada
    como punto, ej. "2.800" = 2800 €; otras ya en euros, ej. "800.000" = 800 €).
    Se detecta por magnitud (< 20 => en miles) y se corrige; se contrastó
    contra superficie/habitaciones para confirmar que el patrón es consistente.
    """
    ruta = _descargar(FOTOCASA_URL, RAW_DIR / "fotocasa_madrid_alicante.csv")
    df = pd.read_csv(ruta, sep=";")
    df.columns = [c.strip() for c in df.columns]

    precio = pd.to_numeric(df["price"], errors="coerce")
    precio = precio.where(precio >= 20, precio * 1000)

    return pd.DataFrame({
        "fecha_publicacion": pd.NaT,
        "precio": precio,
        "superficie_m2": pd.to_numeric(df["surface"], errors="coerce"),
        "habitaciones": pd.to_numeric(df["rooms"], errors="coerce"),
        "banos": pd.to_numeric(df["bathrooms"], errors="coerce"),
        "ciudad": df["city"].str.strip(),
        "zona": df["neighborhood"].fillna(df["district"]).str.strip(),
        "direccion": df["district"],
        "tipo_inmueble": df["buildingType"],
        "url": None,
    })[COLUMNAS_ESTANDAR]


def _extraer_numero(texto: object) -> float:
    if pd.isna(texto):
        return float("nan")
    match = re.search(r"\d+", str(texto))
    return float(match.group()) if match else float("nan")


def cargar_properties_spain() -> pd.DataFrame:
    """Descarga y normaliza properties_Spain.csv (cobertura nacional)."""
    ruta = _descargar(PROPERTIES_SPAIN_URL, RAW_DIR / "properties_spain.csv")
    df = pd.read_csv(ruta)

    return pd.DataFrame({
        "fecha_publicacion": pd.to_datetime(df["Publish_date"], errors="coerce"),
        "precio": pd.to_numeric(df["Sale_Price"], errors="coerce"),
        "superficie_m2": pd.to_numeric(df["Surface"], errors="coerce"),
        "habitaciones": df["Bedrooms"].apply(_extraer_numero),
        "banos": df["Bathrooms"].apply(_extraer_numero),
        "ciudad": df["City"],
        "zona": df["Zone"].fillna(df["City"]),
        "direccion": df["Street"],
        "tipo_inmueble": df["Property_Type"],
        "url": None,
    })[COLUMNAS_ESTANDAR]


def cargar_todo() -> pd.DataFrame:
    """Combina todos los datasets abiertos disponibles en un único DataFrame
    con el esquema estándar del proyecto."""
    fuentes = [cargar_fotocasa_madrid_alicante(), cargar_properties_spain()]
    return pd.concat(fuentes, ignore_index=True)
