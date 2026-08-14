"""Limpieza y normalización de datos de viviendas."""
from __future__ import annotations

import pandas as pd

# precio_m2 de venta (€/m2) y de alquiler (€/mes/m2) son magnitudes distintas
# (mezclarlas en un único umbral descartaría el alquiler entero, ver bug
# corregido en la Fase "datasets abiertos"). "venta" se usa por defecto para
# datos que no traen tipo_operacion (ej. Idealista API, configurada para
# operation=sale).
UMBRALES_PRECIO_M2 = {
    "venta": (300, 20000),
    "alquiler": (3, 60),
}


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia el dataframe crudo de anuncios.

    - Elimina duplicados por URL (o por fila completa si la fuente no trae URL,
      ya que pandas trata NaN == NaN al deduplicar y una columna url vacía
      colapsaría todas las filas en una sola).
    - Descarta filas sin precio o superficie (no se puede calcular precio/m2).
    - Convierte tipos numéricos y fecha.
    - Calcula precio_m2.
    - Descarta outliers evidentes (precio/m2 fuera de un rango razonable,
      distinto para venta y alquiler — ver UMBRALES_PRECIO_M2).
    """
    if df["url"].notna().any():
        df = df.drop_duplicates(subset="url").copy()
    else:
        df = df.drop_duplicates().copy()

    if "tipo_operacion" not in df.columns:
        df["tipo_operacion"] = "venta"
    df["tipo_operacion"] = df["tipo_operacion"].fillna("venta")

    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df["superficie_m2"] = pd.to_numeric(df["superficie_m2"], errors="coerce")
    df["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce").astype("Int64")
    df["banos"] = pd.to_numeric(df["banos"], errors="coerce").astype("Int64")
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")

    df = df.dropna(subset=["precio", "superficie_m2"])
    df = df[df["superficie_m2"] > 0]

    df["precio_m2"] = df["precio"] / df["superficie_m2"]

    minimo = df["tipo_operacion"].map(lambda t: UMBRALES_PRECIO_M2.get(t, UMBRALES_PRECIO_M2["venta"])[0])
    maximo = df["tipo_operacion"].map(lambda t: UMBRALES_PRECIO_M2.get(t, UMBRALES_PRECIO_M2["venta"])[1])
    df = df[(df["precio_m2"] >= minimo) & (df["precio_m2"] <= maximo)]

    return df.reset_index(drop=True)
