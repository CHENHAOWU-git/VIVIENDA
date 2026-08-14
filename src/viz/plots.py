"""Gráficos para el análisis de precios de vivienda (matplotlib).

Paleta categórica de orden fijo (no ciclar colores libremente): cada serie
recibe siempre el mismo slot, para que la identidad de color sea consistente
entre gráficos.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

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


def plot_mapa_precio_m2(df: pd.DataFrame, titulo: str = "Precio/m² por ubicación") -> plt.Figure:
    """Mapa de dispersión geolocalizado: un punto por vivienda (longitud/latitud),
    coloreado por precio_m2 con una rampa secuencial de un solo tono (magnitud).
    Espera columnas longitud, latitud, precio_m2."""
    data = df.dropna(subset=["longitud", "latitud", "precio_m2"])
    # Descarta coordenadas (0, 0) ("Null Island") y otras claramente fuera de
    # España — errores de geocodificación típicos en datasets scrapeados que
    # si no se filtran descuadran la escala del mapa entero.
    data = data[data["latitud"].between(27, 44) & data["longitud"].between(-19, 5)]
    fig, ax = plt.subplots(figsize=(8, 7))
    cmap = LinearSegmentedColormap.from_list("secuencial_azul", SEQUENTIAL_BLUE)
    scatter = ax.scatter(data["longitud"], data["latitud"], c=data["precio_m2"],
                          cmap=cmap, s=40, edgecolors=SURFACE, linewidths=0.5)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Precio/m² (€)", color=INK_SECONDARY)
    cbar.ax.yaxis.set_tick_params(color=INK_MUTED, labelcolor=INK_MUTED)
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_aspect("equal")
    ax.set_title(titulo, color=INK_PRIMARY, loc="left")
    _style_ax(ax)
    fig.tight_layout()
    return fig


def plot_ranking_ciudades(df: pd.DataFrame) -> plt.Figure:
    """Barras: precio/m² relativo a la media de las ciudades presentes en tus
    datos (100 = esa media). Solo usa tu propio snapshot — el IPV del INE es
    un índice de crecimiento desde un año base, no un nivel de precio, así
    que no es comparable directamente contra un precio/m² absoluto (ver
    plot_ipv_evolucion para la tendencia oficial). Espera columnas ciudad,
    indice_propio."""
    data = df.sort_values("indice_propio")
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(data) + 1))
    ax.barh(data["ciudad"], data["indice_propio"], color=CATEGORICAL[0], height=0.6)
    ax.axvline(100, color=INK_MUTED, linewidth=1, linestyle="--")
    ax.set_xlabel("Precio/m² relativo a la media de tus ciudades (100 = media)")
    ax.set_title("Ranking de ciudades en tu snapshot (venta)", color=INK_PRIMARY, loc="left")
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
