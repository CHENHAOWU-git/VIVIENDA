"""Descarga los datasets abiertos de vivienda (sin credenciales), los combina,
limpia y guarda en data/processed/. No requiere ninguna cuenta ni API key.

Uso:
    python scripts/fetch_open_datasets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.clean import clean_listings
from src.data.load import save_processed_csv
from src.data.open_datasets import cargar_todo


def main() -> None:
    print("Descargando datasets abiertos (Fotocasa Madrid+Alicante, properties_Spain)...")
    df_raw = cargar_todo()
    print(f"Total combinado: {len(df_raw)} anuncios (antes de limpiar)")

    df_clean = clean_listings(df_raw)
    out_path = save_processed_csv(df_clean, "open_datasets_clean.csv")
    print(f"Datos limpios guardados en {out_path} ({len(df_clean)} filas)")


if __name__ == "__main__":
    main()
