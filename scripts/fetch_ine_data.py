"""Descarga la evolución del Índice de Precios de Vivienda (INE) para
Nacional + comunidades autónomas seleccionadas, la guarda en
data/processed/ine_ipv.csv y genera un gráfico en outputs/figures/.

Uso:
    python scripts/fetch_ine_data.py
    python scripts/fetch_ine_data.py --regiones Nacional "Madrid, Comunidad de" Cataluña
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.ine_ipv import SERIES_INDICE_GENERAL, obtener_evolucion_por_region
from src.viz.plots import plot_ipv_evolucion

DEFAULT_REGIONES = ["Nacional", "Madrid, Comunidad de", "Cataluña", "Andalucía", "Comunitat Valenciana"]

PROCESSED_DIR = Path("data/processed")
FIGURES_DIR = Path("outputs/figures")


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga y grafica el IPV del INE")
    parser.add_argument("--regiones", nargs="+", default=DEFAULT_REGIONES,
                         choices=list(SERIES_INDICE_GENERAL.keys()),
                         help="Regiones a descargar (máx. 8 recomendado para el gráfico)")
    args = parser.parse_args()

    print(f"Descargando IPV para: {', '.join(args.regiones)}")
    df = obtener_evolucion_por_region(args.regiones)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = PROCESSED_DIR / "ine_ipv.csv"
    df.to_csv(out_csv, index=False)
    print(f"Datos guardados en {out_csv} ({len(df)} filas)")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig = plot_ipv_evolucion(df)
    out_fig = FIGURES_DIR / "ine_ipv_evolucion.png"
    fig.savefig(out_fig, dpi=150)
    print(f"Gráfico guardado en {out_fig}")


if __name__ == "__main__":
    main()
