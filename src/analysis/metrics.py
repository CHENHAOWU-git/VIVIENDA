"""Métricas de análisis: precio/m2, agregaciones y evolución temporal."""
from __future__ import annotations

import pandas as pd


def precio_m2_por_localizacion(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["ciudad", "zona"])["precio_m2"]
        .agg(precio_m2_medio="mean", precio_m2_mediano="median", n_anuncios="count")
        .reset_index()
        .sort_values("precio_m2_medio", ascending=False)
    )


def precio_m2_por_habitaciones(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("habitaciones")["precio_m2"]
        .agg(precio_m2_medio="mean", precio_m2_mediano="median", n_anuncios="count")
        .reset_index()
        .sort_values("habitaciones")
    )


def precio_m2_por_banos(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("banos")["precio_m2"]
        .agg(precio_m2_medio="mean", precio_m2_mediano="median", n_anuncios="count")
        .reset_index()
        .sort_values("banos")
    )


def evolucion_temporal(df: pd.DataFrame, freq: str = "ME", by: str | None = None) -> pd.DataFrame:
    """Evolución del precio/m2 a lo largo del tiempo.

    Args:
        freq: frecuencia de resampleo pandas (ej. "ME" mensual, "QE" trimestral).
        by: columna adicional para desglosar (ej. "ciudad", "zona"). Opcional.
    """
    df = df.dropna(subset=["fecha_publicacion"]).set_index("fecha_publicacion")
    group_cols = [pd.Grouper(freq=freq)]
    if by:
        group_cols.append(by)
    return (
        df.groupby(group_cols)["precio_m2"]
        .agg(precio_m2_medio="mean", precio_m2_mediano="median", n_anuncios="count")
        .reset_index()
    )
