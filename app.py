"""App de visualización del análisis de viviendas (Streamlit).

Uso:
    streamlit run app.py

Requiere haber ejecutado antes (para tener datos):
    python scripts/fetch_open_datasets.py
    python scripts/fetch_ine_data.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Paleta consistente con src/viz/plots.py (misma familia de colores en toda la app)
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

PROCESSED_DIR = Path("data/processed")

st.set_page_config(page_title="Análisis de Viviendas", layout="wide")


@st.cache_data
def cargar_listings() -> pd.DataFrame:
    ruta = PROCESSED_DIR / "open_datasets_clean.csv"
    if not ruta.exists():
        return pd.DataFrame()
    df = pd.read_csv(ruta, parse_dates=["fecha_publicacion"])
    df["id"] = df.index
    return df


@st.cache_data
def cargar_ine() -> pd.DataFrame:
    ruta = PROCESSED_DIR / "ine_ipv.csv"
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_csv(ruta, parse_dates=["periodo"])


def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")
    operacion = st.sidebar.radio("Tipo de operación", ["venta", "alquiler"], horizontal=True)
    df = df[df["tipo_operacion"] == operacion]

    ciudades = sorted(df["ciudad"].dropna().unique())
    seleccion_ciudades = st.sidebar.multiselect("Ciudad", ciudades, default=[])
    if seleccion_ciudades:
        df = df[df["ciudad"].isin(seleccion_ciudades)]

    if not df.empty:
        precio_min, precio_max = float(df["precio_m2"].min()), float(df["precio_m2"].max())
        rango = st.sidebar.slider("Precio/m²", precio_min, precio_max, (precio_min, precio_max))
        df = df[df["precio_m2"].between(*rango)]

        hab_disponibles = sorted(df["habitaciones"].dropna().unique().astype(int))
        if hab_disponibles:
            hab_sel = st.sidebar.multiselect("Habitaciones", hab_disponibles, default=[])
            if hab_sel:
                df = df[df["habitaciones"].isin(hab_sel)]

        banos_disponibles = sorted(df["banos"].dropna().unique().astype(int))
        if banos_disponibles:
            banos_sel = st.sidebar.multiselect("Baños", banos_disponibles, default=[])
            if banos_sel:
                df = df[df["banos"].isin(banos_sel)]

    return df, operacion


def tab_tablas(df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Anuncios", len(df))
    col2.metric("Precio/m² medio", f"{df['precio_m2'].mean():,.0f} €" if len(df) else "—")
    col3.metric("Precio/m² mediano", f"{df['precio_m2'].median():,.0f} €" if len(df) else "—")
    col4.metric("Ciudades", df["ciudad"].nunique())

    st.dataframe(
        df[["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos", "precio_m2", "tipo_inmueble"]]
        .sort_values("precio_m2"),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Precio/m² por ciudad")
    agg = df.groupby("ciudad")["precio_m2"].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(agg, x="precio_m2", y="ciudad", orientation="h",
                 color_discrete_sequence=[CATEGORICAL[0]])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Precio/m² medio (€)", yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Precio/m² por habitaciones")
        agg_hab = df.dropna(subset=["habitaciones"]).groupby("habitaciones")["precio_m2"].mean().reset_index()
        fig_hab = px.bar(agg_hab, x="habitaciones", y="precio_m2", color_discrete_sequence=[CATEGORICAL[0]])
        st.plotly_chart(fig_hab, use_container_width=True)
    with col_b:
        st.subheader("Precio/m² por baños")
        agg_banos = df.dropna(subset=["banos"]).groupby("banos")["precio_m2"].mean().reset_index()
        fig_banos = px.bar(agg_banos, x="banos", y="precio_m2", color_discrete_sequence=[CATEGORICAL[1]])
        st.plotly_chart(fig_banos, use_container_width=True)


def tab_mapa(df: pd.DataFrame) -> None:
    geo = df.dropna(subset=["latitud", "longitud"])
    geo = geo[geo["latitud"].between(27, 44) & geo["longitud"].between(-19, 5)]
    if geo.empty:
        st.info("No hay viviendas con coordenadas para los filtros actuales (las coordenadas solo están disponibles para el alquiler en Madrid y Alicante).")
        return

    centro, zoom = _centro_y_zoom(geo)
    fig = px.scatter_map(
        geo, lat="latitud", lon="longitud", color="precio_m2", size_max=12,
        hover_data=["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos"],
        color_continuous_scale=SEQUENTIAL_BLUE, height=650,
    )
    fig.update_layout(map_style="open-street-map", map_center=centro, map_zoom=zoom,
                       margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)


def _centro_y_zoom(geo: pd.DataFrame) -> tuple[dict, float]:
    """Centro y nivel de zoom que encuadran todos los puntos filtrados.

    px.scatter_map no autoajusta el viewport a los datos (a diferencia de un
    scatter normal): con un zoom fijo, dos clústeres alejados entre sí (ej.
    Madrid + Alicante) pueden quedar ambos fuera de encuadre, centrados en el
    punto medio vacío entre ellos. Se calcula un zoom aproximado a partir del
    rango de coordenadas para que siempre se vean los puntos seleccionados.
    """
    centro = {"lat": geo["latitud"].mean(), "lon": geo["longitud"].mean()}
    rango = max(geo["latitud"].max() - geo["latitud"].min(),
                geo["longitud"].max() - geo["longitud"].min(), 0.01)
    zoom = min(14, max(3, 8.5 - (rango ** 0.3) * 3))
    return centro, zoom


def tab_evolucion_ine() -> None:
    ine = cargar_ine()
    if ine.empty:
        st.info("Ejecuta `python scripts/fetch_ine_data.py` para generar estos datos.")
        return
    fig = go.Figure()
    for i, region in enumerate(ine["region"].unique()):
        subset = ine[ine["region"] == region]
        fig.add_trace(go.Scatter(x=subset["periodo"], y=subset["indice"], name=region,
                                  line=dict(color=CATEGORICAL[i % len(CATEGORICAL)], width=2)))
    fig.update_layout(yaxis_title="Índice de Precios de Vivienda (base INE)", height=550)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Índice de crecimiento desde un año base del INE — no es un precio absoluto en €, por eso se muestra por separado del resto de la app.")


CAMPOS_COMPARACION = [
    ("precio", "Precio total", "menor_mejor", "€"),
    ("precio_m2", "Precio/m²", "menor_mejor", "€/m²"),
    ("superficie_m2", "Superficie", "mayor_mejor", "m²"),
    ("habitaciones", "Habitaciones", "mayor_mejor", ""),
    ("banos", "Baños", "mayor_mejor", ""),
]


def generar_pros_contras(seleccion: pd.DataFrame, media_zona: dict) -> dict:
    pros_contras = {idx: {"pros": [], "contras": []} for idx in seleccion.index}

    for campo, etiqueta, direccion, unidad in CAMPOS_COMPARACION:
        valores = seleccion[campo].dropna()
        if len(valores) < 2:
            continue
        mejor = valores.min() if direccion == "menor_mejor" else valores.max()
        peor = valores.max() if direccion == "menor_mejor" else valores.min()
        if mejor == peor:
            continue
        for idx, valor in valores.items():
            texto = f"{etiqueta}: {valor:,.0f}{unidad}"
            if valor == mejor:
                pros_contras[idx]["pros"].append(f"{texto} (el mejor de los comparados)")
            elif valor == peor:
                pros_contras[idx]["contras"].append(f"{texto} (el peor de los comparados)")

    for idx, fila in seleccion.iterrows():
        zona_media = media_zona.get((fila["ciudad"], fila["zona"]))
        if zona_media and pd.notna(fila["precio_m2"]):
            diferencia = (fila["precio_m2"] / zona_media - 1) * 100
            if diferencia <= -5:
                pros_contras[idx]["pros"].append(f"{abs(diferencia):.0f}% más barato que la media de {fila['zona']}")
            elif diferencia >= 5:
                pros_contras[idx]["contras"].append(f"{diferencia:.0f}% más caro que la media de {fila['zona']}")

    return pros_contras


def tab_comparador(df: pd.DataFrame, contexto: pd.DataFrame) -> None:
    if df.empty:
        st.info("No hay viviendas para los filtros actuales.")
        return

    df = df.copy()
    df["etiqueta"] = (df["ciudad"] + " – " + df["zona"].fillna("") + " · "
                       + df["precio"].map(lambda p: f"{p:,.0f}€") + " · "
                       + df["superficie_m2"].map(lambda s: f"{s:.0f}m²"))

    MAX_COMPARACION = 5  # más columnas de las que caben legibles en pantalla (bug real visto en pruebas)

    opciones = dict(zip(df["etiqueta"], df["id"]))
    seleccionadas = st.multiselect(
        "Elige entre 2 y 5 viviendas para comparar", list(opciones.keys()),
        max_selections=MAX_COMPARACION,
    )

    if len(seleccionadas) < 2:
        st.info("Selecciona al menos 2 viviendas.")
        return

    ids = [opciones[e] for e in seleccionadas]
    seleccion = df[df["id"].isin(ids)].set_index("id")

    media_zona = contexto.groupby(["ciudad", "zona"])["precio_m2"].mean().to_dict()
    pros_contras = generar_pros_contras(seleccion, media_zona)

    tabla = seleccion[["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos", "precio_m2", "tipo_inmueble"]].T
    tabla.columns = [f"Vivienda {i + 1}" for i in range(len(seleccion))]
    st.dataframe(tabla, use_container_width=True)

    columnas = st.columns(len(seleccion))
    for col, (idx, fila) in zip(columnas, seleccion.iterrows()):
        with col:
            st.markdown(f"**{fila['ciudad']} – {fila['zona']}**")
            for pro in pros_contras[idx]["pros"]:
                st.success(f"✅ {pro}", icon=None)
            for contra in pros_contras[idx]["contras"]:
                st.error(f"⚠️ {contra}", icon=None)
            if not pros_contras[idx]["pros"] and not pros_contras[idx]["contras"]:
                st.caption("Sin diferencias destacables frente a las demás seleccionadas.")


def main() -> None:
    st.title("Análisis de Viviendas")

    df_todos = cargar_listings()
    if df_todos.empty:
        st.warning("No hay datos. Ejecuta primero: `python scripts/fetch_open_datasets.py`")
        return

    df_filtrado, operacion = aplicar_filtros(df_todos)
    contexto_operacion = df_todos[df_todos["tipo_operacion"] == operacion]

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tablas y variables", "🗺️ Mapa", "📈 Evolución INE", "⚖️ Comparador"])
    with tab1:
        tab_tablas(df_filtrado)
    with tab2:
        tab_mapa(df_filtrado)
    with tab3:
        tab_evolucion_ine()
    with tab4:
        tab_comparador(df_filtrado, contexto_operacion)


if __name__ == "__main__":
    main()
