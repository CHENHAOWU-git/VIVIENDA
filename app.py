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
MAX_COMPARACION = 5  # más columnas de las que caben legibles en pantalla (bug real visto en pruebas)

# Nombres de columna legibles para mostrar en tablas (los internos se quedan
# en el DataFrame para no romper el resto del código).
COLUMNAS_LEGIBLES = {
    "ciudad": "Ciudad",
    "zona": "Zona",
    "direccion": "Distrito",
    "precio": "Precio (€)",
    "superficie_m2": "Superficie (m²)",
    "habitaciones": "Habitaciones",
    "banos": "Baños",
    "precio_m2": "Precio/m² (€)",
    "tipo_inmueble": "Tipo de inmueble",
    "tipo_operacion": "Operación",
}

st.set_page_config(page_title="Análisis de Viviendas", layout="wide", page_icon="🏠")


def _mostrar(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia con las columnas renombradas a algo legible, solo
    para pintar en pantalla (no usar el resultado para cálculos)."""
    return df.rename(columns=COLUMNAS_LEGIBLES)


@st.cache_data(ttl=86400)
def cargar_listings() -> pd.DataFrame:
    """Lee el CSV ya generado si existe (uso local normal); si no (ej. un
    despliegue recién clonado, donde open_datasets_clean.csv no está en git
    porque se regenera localmente), descarga y limpia los datos al vuelo."""
    ruta = PROCESSED_DIR / "open_datasets_clean.csv"
    if ruta.exists():
        df = pd.read_csv(ruta, parse_dates=["fecha_publicacion"])
    else:
        from src.data.clean import clean_listings
        from src.data.open_datasets import cargar_todo
        df = clean_listings(cargar_todo())
    df["id"] = df.index.astype(str)
    return df


@st.cache_data(ttl=86400)
def cargar_ine() -> pd.DataFrame:
    """El IPV sí está versionado en git (ver .gitignore), pero por si acaso
    se ejecuta en un sitio donde no llegó a clonarse, también tiene fallback."""
    ruta = PROCESSED_DIR / "ine_ipv.csv"
    if ruta.exists():
        return pd.read_csv(ruta, parse_dates=["periodo"])
    from src.data.ine_ipv import obtener_evolucion_por_region
    return obtener_evolucion_por_region()


def aplicar_filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    st.sidebar.header("🔍 Filtros")
    operacion = st.sidebar.radio(
        "¿Qué buscas?", ["venta", "alquiler"], horizontal=True,
        help="El precio/m² de venta y alquiler son magnitudes distintas (€/m² vs €/mes/m²) y nunca se mezclan.",
    )
    df = df[df["tipo_operacion"] == operacion]

    ciudades = sorted(df["ciudad"].dropna().unique())
    seleccion_ciudades = st.sidebar.multiselect("Ciudad", ciudades, default=[],
                                                 help="Vacío = todas las ciudades")
    if seleccion_ciudades:
        df = df[df["ciudad"].isin(seleccion_ciudades)]

    if not df.empty:
        precio_min, precio_max = float(df["precio_m2"].min()), float(df["precio_m2"].max())
        unidad = "€/m²" if operacion == "venta" else "€/mes/m²"
        rango = st.sidebar.slider(f"Precio/m² ({unidad})", precio_min, precio_max, (precio_min, precio_max))
        df = df[df["precio_m2"].between(*rango)]

        with st.sidebar.expander("Más filtros"):
            hab_disponibles = sorted(df["habitaciones"].dropna().unique().astype(int))
            if hab_disponibles:
                hab_sel = st.multiselect("Habitaciones", hab_disponibles, default=[])
                if hab_sel:
                    df = df[df["habitaciones"].isin(hab_sel)]

            banos_disponibles = sorted(df["banos"].dropna().unique().astype(int))
            if banos_disponibles:
                banos_sel = st.multiselect("Baños", banos_disponibles, default=[])
                if banos_sel:
                    df = df[df["banos"].isin(banos_sel)]

    st.sidebar.divider()
    st.sidebar.metric("Viviendas con estos filtros", len(df))

    return df, operacion


def tab_tablas(df: pd.DataFrame) -> None:
    st.caption("Explora el listado completo y compara precios entre ciudades, habitaciones y baños.")

    if df.empty:
        st.warning("Ningún anuncio cumple estos filtros. Prueba a ampliar el rango de precio o quitar algún filtro en la barra lateral.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Anuncios", len(df))
    col2.metric("Precio/m² medio", f"{df['precio_m2'].mean():,.0f} €")
    col3.metric("Precio/m² mediano", f"{df['precio_m2'].median():,.0f} €")
    col4.metric("Ciudades", df["ciudad"].nunique())

    st.dataframe(
        _mostrar(df[["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos", "precio_m2", "tipo_inmueble"]]
                 .sort_values("precio_m2")),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Precio/m² por ciudad")
    agg = df.groupby("ciudad")["precio_m2"].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(agg, x="precio_m2", y="ciudad", orientation="h",
                 color_discrete_sequence=[CATEGORICAL[0]],
                 labels={"precio_m2": "Precio/m² medio (€)", "ciudad": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Precio/m² por habitaciones")
        agg_hab = df.dropna(subset=["habitaciones"]).groupby("habitaciones")["precio_m2"].mean().reset_index()
        fig_hab = px.bar(agg_hab, x="habitaciones", y="precio_m2", color_discrete_sequence=[CATEGORICAL[0]],
                          labels={"precio_m2": "Precio/m² medio (€)", "habitaciones": "Habitaciones"})
        st.plotly_chart(fig_hab, use_container_width=True)
    with col_b:
        st.subheader("Precio/m² por baños")
        agg_banos = df.dropna(subset=["banos"]).groupby("banos")["precio_m2"].mean().reset_index()
        fig_banos = px.bar(agg_banos, x="banos", y="precio_m2", color_discrete_sequence=[CATEGORICAL[1]],
                            labels={"precio_m2": "Precio/m² medio (€)", "banos": "Baños"})
        st.plotly_chart(fig_banos, use_container_width=True)


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


def tab_mapa(df: pd.DataFrame) -> None:
    st.caption("Mapa por ubicación exacta. Solo disponible para el alquiler en Madrid y Alicante (únicas ciudades con coordenadas en los datos actuales).")

    geo = df.dropna(subset=["latitud", "longitud"])
    geo = geo[geo["latitud"].between(27, 44) & geo["longitud"].between(-19, 5)]
    if geo.empty:
        st.info("💡 Prueba a cambiar el filtro **¿Qué buscas?** de la barra lateral a **alquiler** y sin filtrar por ciudad, para ver el mapa.")
        return

    centro, zoom = _centro_y_zoom(geo)
    fig = px.scatter_map(
        geo, lat="latitud", lon="longitud", color="precio_m2", size_max=12,
        hover_data=["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos"],
        color_continuous_scale=SEQUENTIAL_BLUE, height=650,
        labels={"precio_m2": "Precio/m²"},
    )
    fig.update_layout(map_style="open-street-map", map_center=centro, map_zoom=zoom,
                       margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)


def tab_evolucion_ine() -> None:
    st.caption("Tendencia oficial del mercado, publicada trimestralmente por el INE.")

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
    st.info("ℹ️ Es un índice de crecimiento desde un año base, no un precio en €, así que no es comparable directamente contra el precio/m² del resto de la app.")


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


def _total_en_comparacion() -> int:
    return len(st.session_state.get("comparador_seleccion", [])) + len(st.session_state.get("viviendas_manuales", []))


def _formulario_manual(operacion: str) -> None:
    al_maximo = _total_en_comparacion() >= MAX_COMPARACION
    with st.expander("➕ Añadir una vivienda manualmente (si no está en los datos)", expanded=False):
        st.caption("Útil para comparar una oferta real que hayas visto en un portal y que no esté en nuestros datasets.")
        if al_maximo:
            st.warning(f"Ya tienes {MAX_COMPARACION} viviendas en la comparación. Quita alguna antes de añadir otra.")

        with st.form("form_manual", clear_on_submit=True, border=False):
            col1, col2 = st.columns(2)
            with col1:
                ciudad = st.text_input("Ciudad *")
                zona = st.text_input("Zona / barrio")
                precio = st.number_input("Precio (€) *", min_value=0.0, step=1000.0, format="%.0f")
            with col2:
                superficie = st.number_input("Superficie (m²) *", min_value=0.0, step=1.0, format="%.0f")
                habitaciones = st.number_input("Habitaciones", min_value=0, step=1)
                banos = st.number_input("Baños", min_value=0, step=1)
            tipo = st.text_input("Tipo de inmueble", value="")

            enviado = st.form_submit_button("Añadir a la comparación", disabled=al_maximo, use_container_width=True)
            if enviado:
                if not ciudad.strip() or precio <= 0 or superficie <= 0:
                    st.error("Rellena al menos ciudad, precio y superficie (mayores que 0).")
                else:
                    nueva = {
                        "id": f"manual-{len(st.session_state.viviendas_manuales)}",
                        "ciudad": ciudad.strip(),
                        "zona": zona.strip() or ciudad.strip(),
                        "precio": precio,
                        "superficie_m2": superficie,
                        "habitaciones": habitaciones or None,
                        "banos": banos or None,
                        "tipo_inmueble": tipo.strip() or "Manual",
                        "precio_m2": precio / superficie,
                        "tipo_operacion": operacion,
                        "direccion": None,
                    }
                    st.session_state.viviendas_manuales.append(nueva)
                    st.success(f"Añadida: {nueva['ciudad']} – {nueva['zona']}")
                    st.rerun()


def tab_comparador(df: pd.DataFrame, contexto: pd.DataFrame, operacion: str) -> None:
    st.caption("Elige viviendas del listado y/o añade las tuyas manualmente. Obtén pros y contras automáticos entre las comparadas.")

    st.session_state.setdefault("viviendas_manuales", [])

    df = df.copy()
    df["etiqueta"] = (df["ciudad"] + " – " + df["zona"].fillna("") + " · "
                       + df["precio"].map(lambda p: f"{p:,.0f}€") + " · "
                       + df["superficie_m2"].map(lambda s: f"{s:.0f}m²"))
    opciones = dict(zip(df["etiqueta"], df["id"]))

    espacio_dataset = MAX_COMPARACION - len(st.session_state.viviendas_manuales)
    seleccionadas = st.multiselect(
        f"Elige viviendas del listado (máx. {MAX_COMPARACION} entre listado + manuales)",
        list(opciones.keys()), max_selections=max(espacio_dataset, 0),
        key="comparador_seleccion",
    )

    _formulario_manual(operacion)

    if st.session_state.viviendas_manuales:
        st.caption("**Viviendas añadidas manualmente:**")
        for i, v in enumerate(st.session_state.viviendas_manuales):
            c1, c2 = st.columns([6, 1])
            c1.write(f"🏠 {v['ciudad']} – {v['zona']} · {v['precio']:,.0f}€ · {v['superficie_m2']:.0f}m²")
            if c2.button("Quitar", key=f"quitar_manual_{i}"):
                st.session_state.viviendas_manuales.pop(i)
                st.rerun()

    ids = [opciones[e] for e in seleccionadas]
    seleccion_dataset = df[df["id"].isin(ids)].set_index("id")
    manual_df = pd.DataFrame(st.session_state.viviendas_manuales).set_index("id") if st.session_state.viviendas_manuales else pd.DataFrame()
    seleccion = pd.concat([seleccion_dataset, manual_df]) if not manual_df.empty else seleccion_dataset

    if len(seleccion) < 2:
        st.info("Selecciona al menos 2 viviendas (del listado y/o manuales) para ver la comparación.")
        return

    media_zona = contexto.groupby(["ciudad", "zona"])["precio_m2"].mean().to_dict()
    pros_contras = generar_pros_contras(seleccion, media_zona)

    columnas_tabla = ["ciudad", "zona", "precio", "superficie_m2", "habitaciones", "banos", "precio_m2", "tipo_inmueble"]
    tabla = _mostrar(seleccion[columnas_tabla]).T
    tabla.columns = [f"Vivienda {i + 1}" for i in range(len(seleccion))]
    st.dataframe(tabla, use_container_width=True)

    columnas = st.columns(len(seleccion))
    for col, (idx, fila) in zip(columnas, seleccion.iterrows()):
        with col:
            origen = " (manual)" if str(idx).startswith("manual-") else ""
            st.markdown(f"**{fila['ciudad']} – {fila['zona']}{origen}**")
            for pro in pros_contras[idx]["pros"]:
                st.success(f"✅ {pro}")
            for contra in pros_contras[idx]["contras"]:
                st.error(f"⚠️ {contra}")
            if not pros_contras[idx]["pros"] and not pros_contras[idx]["contras"]:
                st.caption("Sin diferencias destacables frente a las demás seleccionadas.")


def main() -> None:
    st.title("🏠 Análisis de Viviendas")
    with st.expander("ℹ️ Cómo usar esta app", expanded=False):
        st.markdown(
            "1. Elige **venta** o **alquiler** y ajusta los filtros en la barra lateral.\n"
            "2. **📋 Tablas y variables** — el listado completo y cómo varía el precio/m² por ciudad, habitaciones y baños.\n"
            "3. **🗺️ Mapa** — ubicación exacta de cada vivienda (solo alquiler en Madrid/Alicante, únicas con coordenadas).\n"
            "4. **📈 Evolución INE** — tendencia oficial del mercado a lo largo del tiempo, para contexto.\n"
            "5. **⚖️ Comparador** — elige hasta 5 viviendas (del listado o añadidas a mano) y obtén sus pros y contras automáticamente."
        )

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
        tab_comparador(df_filtrado, contexto_operacion, operacion)


if __name__ == "__main__":
    main()
