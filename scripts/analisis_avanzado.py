"""Análisis avanzado: mapa geolocalizado de precio/m2 y comparativa contra la
referencia oficial del INE. Requiere haber ejecutado antes:
    python scripts/fetch_open_datasets.py

Uso:
    python scripts/analisis_avanzado.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data.ine_ipv import obtener_evolucion_por_region
from src.viz.plots import plot_ipv_evolucion, plot_mapa_precio_m2, plot_ranking_ciudades

PROCESSED_DIR = Path("data/processed")
FIGURES_DIR = Path("outputs/figures")

# Comunidad autónoma de cada ciudad presente en el dataset de venta (debe
# coincidir con las claves de src/data/ine_ipv.SERIES_INDICE_GENERAL). Si
# aparecen ciudades nuevas al combinar más fuentes, hay que añadirlas aquí.
CIUDAD_A_CCAA = {
    "Alicante": "Comunitat Valenciana",
    "Almería": "Andalucía",
    "Badajoz": "Extremadura",
    "Barcelona": "Cataluña",
    "Bilbao": "País Vasco",
    "Cordoba": "Andalucía",
    "Cádiz": "Andalucía",
    "Granada": "Andalucía",
    "Huelva": "Andalucía",
    "Jaén": "Andalucía",
    "Madrid": "Madrid, Comunidad de",
    "Málaga": "Andalucía",
    "Santa Cruz De Tenerife": "Canarias",
    "Sevilla": "Andalucía",
    "Tarragona": "Cataluña",
    "Toledo": "Castilla - La Mancha",
    "Valencia": "Comunitat Valenciana",
    "Valladolid": "Castilla y León",
    "Zaragoza": "Aragón",
}


def generar_mapa(df: pd.DataFrame) -> None:
    alquiler_geo = df[(df["tipo_operacion"] == "alquiler") & df["latitud"].notna()]
    if alquiler_geo.empty:
        print("Sin filas con coordenadas para el mapa, se omite.")
        return
    fig = plot_mapa_precio_m2(alquiler_geo, titulo="Alquiler: precio/m² por ubicación (Madrid + Alicante)")
    out = FIGURES_DIR / "mapa_precio_m2_alquiler.png"
    fig.savefig(out, dpi=150)
    print(f"Mapa guardado en {out} ({len(alquiler_geo)} viviendas)")


def generar_ranking_y_tendencia_ine(df: pd.DataFrame) -> None:
    """Dos análisis deliberadamente separados (no superpuestos):

    1. Ranking de ciudades según tu propio snapshot (precio/m² relativo).
    2. Tendencia oficial del INE para esas mismas comunidades autónomas.

    No se combinan en un mismo gráfico porque miden magnitudes distintas: el
    IPV del INE es un índice de crecimiento desde un año base (no un precio
    absoluto), así que no es comparable directamente contra tu precio/m².
    """
    venta = df[df["tipo_operacion"] == "venta"].copy()
    venta["comunidad_autonoma"] = venta["ciudad"].map(CIUDAD_A_CCAA)

    sin_mapear = venta[venta["comunidad_autonoma"].isna()]["ciudad"].unique()
    if len(sin_mapear):
        print(f"Aviso: ciudades sin comunidad autónoma mapeada, se excluyen: {list(sin_mapear)}")
    venta = venta.dropna(subset=["comunidad_autonoma"])

    media_propia = venta["precio_m2"].mean()
    por_ciudad = venta.groupby("ciudad").agg(
        precio_m2_medio=("precio_m2", "mean"),
        comunidad_autonoma=("comunidad_autonoma", "first"),
        n_anuncios=("precio_m2", "count"),
    ).reset_index()
    por_ciudad["indice_propio"] = por_ciudad["precio_m2_medio"] / media_propia * 100

    fig_ranking = plot_ranking_ciudades(por_ciudad)
    out_ranking = FIGURES_DIR / "ranking_ciudades.png"
    fig_ranking.savefig(out_ranking, dpi=150)
    print(f"Ranking guardado en {out_ranking}")
    print(por_ciudad[["ciudad", "comunidad_autonoma", "n_anuncios", "precio_m2_medio", "indice_propio"]]
          .sort_values("indice_propio", ascending=False).to_string(index=False))

    # plot_ipv_evolucion limita a 8 series (paleta categórica de orden fijo);
    # si hay más comunidades que eso, se priorizan las que tienen más
    # anuncios en tu propio snapshot en vez de cortar alfabéticamente (lo que
    # descartaba silenciosamente Madrid, tu ciudad con más peso).
    anuncios_por_region = por_ciudad.groupby("comunidad_autonoma")["n_anuncios"].sum()
    regiones_necesarias = anuncios_por_region.sort_values(ascending=False).head(8).index.tolist()
    ine = obtener_evolucion_por_region(regiones_necesarias)
    fig_ine = plot_ipv_evolucion(ine)
    out_ine = FIGURES_DIR / "ipv_comunidades_snapshot.png"
    fig_ine.savefig(out_ine, dpi=150)
    print(f"\nTendencia oficial del INE (mismas comunidades) guardada en {out_ine}")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "open_datasets_clean.csv", parse_dates=["fecha_publicacion"])

    generar_mapa(df)
    print()
    generar_ranking_y_tendencia_ine(df)


if __name__ == "__main__":
    main()
