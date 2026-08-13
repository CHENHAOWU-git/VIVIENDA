"""Gráficos para el análisis de precios de vivienda (matplotlib).

Paleta categórica de orden fijo (no ciclar colores libremente): cada serie
recibe siempre el mismo slot, para que la identidad de color sea consistente
entre gráficos.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"


def _style_ax(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRIDLINE)
    ax.tick_params(colors=INK_MUTED)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def plot_precio_m2_por_zona(agg: pd.DataFrame, top_n: int = 15) -> plt.Figure:
    """Barra horizontal: precio/m2 medio por zona, top N zonas más caras."""
    data = agg.nlargest(top_n, "precio_m2_medio").sort_values("precio_m2_medio")
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(data) + 1))
    ax.barh(data["zona"] + " (" + data["ciudad"] + ")", data["precio_m2_medio"],
            color=CATEGORICAL[0], height=0.6)
    ax.set_xlabel("Precio medio por m² (€)")
    ax.set_title("Precio/m² por zona", color=INK_PRIMARY, loc="left")
    _style_ax(ax)
    fig.tight_layout()
    return fig


def plot_precio_m2_por_habitaciones(agg: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(agg["habitaciones"].astype(str), agg["precio_m2_medio"], color=CATEGORICAL[0], width=0.6)
    ax.set_xlabel("Habitaciones")
    ax.set_ylabel("Precio medio por m² (€)")
    ax.set_title("Precio/m² por número de habitaciones", color=INK_PRIMARY, loc="left")
    _style_ax(ax)
    fig.tight_layout()
    return fig


def plot_ipv_evolucion(df: pd.DataFrame) -> plt.Figure:
    """Evolución del Índice de Precios de Vivienda (INE). Espera columnas
    periodo, region, indice (ver src/data/ine_ipv.obtener_evolucion_por_region).
    Máximo 8 regiones (límite de la paleta categórica de orden fijo)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    regiones = df["region"].unique()[:8]
    for i, region in enumerate(regiones):
        subset = df[df["region"] == region]
        ax.plot(subset["periodo"], subset["indice"], label=region,
                color=CATEGORICAL[i % len(CATEGORICAL)], linewidth=2)

    ax.set_ylabel("Índice de Precios de Vivienda (base INE)")
    ax.set_title("Evolución del IPV por comunidad autónoma", color=INK_PRIMARY, loc="left")
    ax.legend(frameon=False, labelcolor=INK_SECONDARY)
    _style_ax(ax)
    fig.tight_layout()
    return fig


def plot_evolucion_temporal(evol: pd.DataFrame, by: str | None = None) -> plt.Figure:
    """Línea de evolución temporal. Si `by` está presente, una línea por categoría
    (máximo 8 categorías — usa la paleta categórica en orden fijo)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    time_col = evol.columns[0]

    if by:
        categorias = evol[by].dropna().unique()[:8]
        for i, cat in enumerate(categorias):
            subset = evol[evol[by] == cat]
            ax.plot(subset[time_col], subset["precio_m2_medio"], label=str(cat),
                    color=CATEGORICAL[i % len(CATEGORICAL)], linewidth=2)
        ax.legend(frameon=False, labelcolor=INK_SECONDARY)
    else:
        ax.plot(evol[time_col], evol["precio_m2_medio"], color=CATEGORICAL[0], linewidth=2)

    ax.set_ylabel("Precio medio por m² (€)")
    ax.set_title("Evolución del precio/m²", color=INK_PRIMARY, loc="left")
    _style_ax(ax)
    fig.tight_layout()
    return fig
