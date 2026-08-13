"""Pipeline end-to-end: scrape -> clean -> analyze.

Uso:
    python scripts/run_pipeline.py --step scrape
    python scripts/run_pipeline.py --step clean --input anuncios_raw.csv --output anuncios_clean.csv
    python scripts/run_pipeline.py --step analyze --input anuncios_clean.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from src.data.clean import clean_listings
from src.data.load import load_processed_csv, load_raw_csv, save_processed_csv
from src.analysis.metrics import (
    evolucion_temporal,
    precio_m2_por_banos,
    precio_m2_por_habitaciones,
    precio_m2_por_localizacion,
)


def load_config() -> dict:
    with open("config/settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def step_scrape() -> None:
    print(
        "El scraping depende del portal elegido. Implementa la lógica de "
        "recorrido de páginas en src/scraper/scraper.py (parse_listing_html) "
        "y guarda el resultado como CSV en data/raw/."
    )


def step_clean(input_file: str, output_file: str) -> None:
    df_raw = load_raw_csv(input_file)
    df_clean = clean_listings(df_raw)
    out_path = save_processed_csv(df_clean, output_file)
    print(f"Datos limpios guardados en {out_path} ({len(df_clean)} filas)")


def step_analyze(input_file: str) -> None:
    df = load_processed_csv(input_file)

    print("\n== Precio/m2 por localización (top 10) ==")
    print(precio_m2_por_localizacion(df).head(10).to_string(index=False))

    print("\n== Precio/m2 por habitaciones ==")
    print(precio_m2_por_habitaciones(df).to_string(index=False))

    print("\n== Precio/m2 por baños ==")
    print(precio_m2_por_banos(df).to_string(index=False))

    print("\n== Evolución temporal (mensual) ==")
    print(evolucion_temporal(df, freq="ME").to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de análisis de viviendas")
    parser.add_argument("--step", required=True, choices=["scrape", "clean", "analyze"])
    parser.add_argument("--input", default="anuncios_raw.csv")
    parser.add_argument("--output", default="anuncios_clean.csv")
    args = parser.parse_args()

    if args.step == "scrape":
        step_scrape()
    elif args.step == "clean":
        step_clean(args.input, args.output)
    elif args.step == "analyze":
        step_analyze(args.input)


if __name__ == "__main__":
    main()
