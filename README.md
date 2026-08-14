# Análisis de Viviendas

Proyecto para analizar precios de viviendas y su evolución en función de:
- Precio por m²
- Número de habitaciones
- Número de baños
- Localización (barrio/ciudad)
- Evolución temporal del precio

## Estructura del proyecto

```
analisis-viviendas/
├── config/             # Configuración (portales, ciudades, rutas)
│   └── settings.yaml
├── data/
│   ├── raw/            # Datos crudos, tal como se obtienen (no editar a mano)
│   ├── processed/      # Datos limpios, listos para analizar
│   └── external/       # Datos auxiliares (ej. códigos postales, distritos)
├── notebooks/          # Exploración y análisis interactivo
├── src/
│   ├── scraper/        # Obtención de datos desde el portal inmobiliario
│   ├── data/           # Carga y limpieza de datos
│   ├── analysis/       # Cálculo de métricas (precio/m2, evolución, etc.)
│   └── viz/            # Generación de gráficos
├── scripts/             # Scripts ejecutables (pipeline end-to-end)
├── tests/               # Tests unitarios
└── outputs/
    ├── figures/         # Gráficos generados
    └── reports/         # Informes/resúmenes generados
```

## Fuentes de datos

| Fuente | Acceso | Qué aporta | Notas |
|---|---|---|---|
| **Datasets abiertos (Zenodo)** (`src/data/open_datasets.py`) | Libre, **sin cuenta ni credenciales** — descarga directa de CSV | Anuncios individuales: precio, m², habitaciones, baños, ciudad/barrio | Fuente por defecto del proyecto. Ver detalle abajo. |
| **INE — Índice de Precios de Vivienda** (`src/data/ine_ipv.py`) | Abierto, sin registro ([API Tempus3](https://www.ine.es/dyngs/DAB/index.htm?cid=1100) / [datos.gob.es](https://datos.gob.es/es/catalogo/ea0042823-indice-de-precios-de-la-vivienda-ipv)) | Evolución trimestral oficial del precio de vivienda por comunidad autónoma/provincia (nueva/segunda mano) | Agregado, no por vivienda individual — ideal para contrastar tus datos con la referencia oficial. |
| **Idealista API** (`src/scraper/idealista_api.py`) | Oficial, requiere solicitud en [developers.idealista.com](https://developers.idealista.com/access-request) (apikey + secret) | Anuncios individuales, actualizados en tiempo real | Opcional, para cuando tengas credenciales y quieras datos más recientes/tu propia zona exacta. |
| Catastro (Sede Electrónica) | Abierto para datos no protegidos | Superficie, uso, ubicación catastral | **No incluye precios**. |
| Fotocasa (API oficial) | Sin API pública de consulta (solo pública para publicar anuncios propios) | — | El acceso a datos de mercado en tiempo real es de pago (Fotocasa Pro Data). No usar scraping de su web sin autorización explícita. |
| `src/scraper/scraper.py` (HTML genérico) | Último recurso | — | Solo para portales sin API oficial que permitan expresamente el scraping en su `robots.txt`/ToS. Revísalo caso por caso. |

### Datasets abiertos incluidos (sin credenciales)

`src/data/open_datasets.py` descarga y combina dos datasets ya publicados, con acceso libre y descarga directa (sin registro):

1. **Fotocasa — alquiler, Madrid + Alicante por barrio.** Rezzak Liman, O. (2021). [doi.org/10.5281/zenodo.5599647](https://doi.org/10.5281/zenodo.5599647) — CC-BY 4.0 (requiere atribución).
   - *Nota de calidad de datos*: el CSV original mezcla dos formatos de precio (algunas filas en miles de € exportadas con `.` como separador, ej. `2.800` = 2800 €; otras ya en € directos, ej. `800.000` = 800 €). Se corrige por magnitud en el loader (`< 20` ⇒ multiplicar ×1000); se validó cruzando contra superficie/habitaciones antes de aplicar la corrección.
2. **properties_Spain.csv — venta/alquiler, cobertura nacional.** [doi.org/10.5281/zenodo.14028180](https://doi.org/10.5281/zenodo.14028180) — MIT.

Otros datasets evaluados y descartados por no cumplir precio+m²+habitaciones+baños+zona a nivel de vivienda individual sin cuenta: `Data-Market/inmuebles-en-venta` (sin baños), `idealista18` (tiene todo pero solo se distribuye como paquete R — se probó leerlo desde Python con la librería `rdata`, funciona para los datos de la vivienda pero no para los polígonos de barrio por un bug de codificación en esa librería), datasets de Mendeley de Madrid/Teruel (agregados por barrio, no por vivienda individual).

### Venta vs. alquiler — no mezclar el precio/m²

Los datasets combinados incluyen tanto venta (€/m²) como alquiler (€/mes/m²): son magnitudes distintas y **nunca deben promediarse juntas**. Por eso:
- `clean_listings()` guarda `tipo_operacion` (`venta`/`alquiler`) y aplica un rango de outliers distinto a cada una (`UMBRALES_PRECIO_M2` en `src/data/clean.py`) — con un único umbral pensado para venta, el alquiler entero se descartaba por completo (bug real, corregido).
- Cualquier agregación (`precio_m2_por_*`, gráficos) debe filtrar antes por `tipo_operacion`.
- El IPV del INE es un **índice de crecimiento** desde un año base, no un precio absoluto — tampoco es comparable directamente contra tu precio/m² en €. `scripts/analisis_avanzado.py` los muestra siempre en gráficos separados, nunca superpuestos.

### Reglas generales
1. Los datasets abiertos son snapshots estáticos (no se actualizan solos) — para evolución temporal propia, vuelve a descargarlos/combínalos periódicamente o usa la API de Idealista cuando tengas credenciales.
2. Si decides scrapear un portal sin API, revisa antes `robots.txt` y los Términos de Servicio del sitio concreto.
3. Guarda credenciales (`IDEALISTA_API_KEY`, `IDEALISTA_API_SECRET`) como variables de entorno, nunca en el repo (ver `.gitignore`, `config/secrets.yaml` está excluido).
4. Cita las fuentes de los datasets abiertos si compartes o publicas los resultados (ver licencias arriba).

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

### Anuncios individuales (datasets abiertos, sin credenciales — recomendado para empezar)

```powershell
python scripts/fetch_open_datasets.py
```

Descarga y combina los datasets de la sección anterior, limpia el resultado y lo guarda en `data/processed/open_datasets_clean.csv`. Explóralo en `notebooks/03_open_datasets.ipynb`.

### Análisis avanzado: mapa y ranking (sin credenciales)

```powershell
python scripts/analisis_avanzado.py
```

Requiere haber ejecutado antes `fetch_open_datasets.py`. Genera:
- `outputs/figures/mapa_precio_m2_alquiler.png` — mapa geolocalizado del alquiler (Madrid + Alicante, únicas ciudades con coordenadas en los datasets actuales).
- `outputs/figures/ranking_ciudades.png` — ranking de ciudades por precio/m² de venta, relativo a la media de tu propio snapshot.
- `outputs/figures/ipv_comunidades_snapshot.png` — tendencia oficial del INE para las comunidades autónomas con más peso en tu snapshot (contexto, no superpuesto con lo anterior — ver nota sobre venta/alquiler arriba).

Notebook equivalente: `notebooks/04_analisis_avanzado.ipynb`.

### Evolución oficial del mercado (INE, sin credenciales)

```powershell
python scripts/fetch_ine_data.py
```

Descarga el Índice de Precios de Vivienda del INE (Nacional + comunidades autónomas), lo guarda en `data/processed/ine_ipv.csv` y genera `outputs/figures/ine_ipv_evolucion.png`. Explora el resultado en `notebooks/02_ine_evolucion.ipynb`. Elige otras regiones con `--regiones "Nacional" "País Vasco" ...` (ver claves válidas en `src/data/ine_ipv.SERIES_INDICE_GENERAL`).

### Anuncios individuales (Idealista API, requiere credenciales)

1. Configura el portal/ciudad/rango en `config/settings.yaml`.
2. Ejecuta el scraper: `python scripts/run_pipeline.py --step scrape`
3. Limpia los datos: `python scripts/run_pipeline.py --step clean`
4. Analiza: abre los notebooks en `notebooks/` o ejecuta `python scripts/run_pipeline.py --step analyze`

## Métricas calculadas

- Precio medio y mediano por m²
- Precio por m² según nº de habitaciones y baños
- Evolución temporal del precio/m² por localización
- Comparativa entre barrios/zonas
