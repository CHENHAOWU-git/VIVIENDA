"""Carga de datos crudos y procesados."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

COLUMNAS_ESPERADAS = [
    "fecha_publicacion", "precio", "superficie_m2", "habitaciones",
    "banos", "ciudad", "zona", "direccion", "tipo_inmueble", "url",
]


def load_raw_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    df = pd.read_csv(path)
    faltantes = set(COLUMNAS_ESPERADAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas esperadas en {filename}: {faltantes}")
    return df


def save_processed_csv(df: pd.DataFrame, filename: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / filename
    df.to_csv(out_path, index=False)
    return out_path


def load_processed_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / filename, parse_dates=["fecha_publicacion"])
