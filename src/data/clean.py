"""Limpieza y normalización de datos de viviendas."""
from __future__ import annotations

import pandas as pd


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia el dataframe crudo de anuncios.

    - Elimina duplicados por URL (o por fila completa si la fuente no trae URL,
      ya que pandas trata NaN == NaN al deduplicar y una columna url vacía
      colapsaría todas las filas en una sola).
    - Descarta filas sin precio o superficie (no se puede calcular precio/m2).
    - Convierte tipos numéricos y fecha.
    - Calcula precio_m2.
    - Descarta outliers evidentes (precio/m2 fuera de un rango razonable).
    """
    if df["url"].notna().any():
        df = df.drop_duplicates(subset="url").copy()
    else:
        df = df.drop_duplicates().copy()

    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df["superficie_m2"] = pd.to_numeric(df["superficie_m2"], errors="coerce")
    df["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce").astype("Int64")
    df["banos"] = pd.to_numeric(df["banos"], errors="coerce").astype("Int64")
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")

    df = df.dropna(subset=["precio", "superficie_m2"])
    df = df[df["superficie_m2"] > 0]

    df["precio_m2"] = df["precio"] / df["superficie_m2"]

    # Outliers evidentes: fuera de este rango probablemente son errores de scraping
    df = df[(df["precio_m2"] >= 300) & (df["precio_m2"] <= 20000)]

    return df.reset_index(drop=True)
