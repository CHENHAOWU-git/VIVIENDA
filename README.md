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
| **Idealista API** (`src/scraper/idealista_api.py`) | Oficial, requiere solicitud en [developers.idealista.com](https://developers.idealista.com/access-request) (apikey + secret) | Anuncios individuales: precio, m², habitaciones, baños, localización | Vía legal recomendada frente al scraping de HTML. Cuota mensual gratuita limitada — revisa tu panel de desarrollador. |
| **INE — Índice de Precios de Vivienda** (`src/data/ine_ipv.py`) | Abierto, sin registro ([API Tempus3](https://www.ine.es/dyngs/DAB/index.htm?cid=1100) / [datos.gob.es](https://datos.gob.es/es/catalogo/ea0042823-indice-de-precios-de-la-vivienda-ipv)) | Evolución trimestral oficial del precio de vivienda por comunidad autónoma/provincia (nueva/segunda mano) | Agregado, no por vivienda individual — ideal para contrastar tus datos con la referencia oficial. |
| Catastro (Sede Electrónica) | Abierto para datos no protegidos | Superficie, uso, ubicación catastral | **No incluye precios**. |
| Fotocasa | Sin API pública de consulta (solo pública para publicar anuncios propios) | — | El acceso a datos de mercado es de pago (Fotocasa Pro Data). No usar scraping de su web sin autorización explícita. |
| `src/scraper/scraper.py` (HTML genérico) | Último recurso | — | Solo para portales sin API oficial que permitan expresamente el scraping en su `robots.txt`/ToS. Revísalo caso por caso. |

### Reglas generales
1. Prioriza siempre la vía oficial (API) sobre el scraping de HTML.
2. Si no hay API y decides scrapear, revisa antes `robots.txt` y los Términos de Servicio del sitio concreto.
3. Guarda credenciales (`IDEALISTA_API_KEY`, `IDEALISTA_API_SECRET`) como variables de entorno, nunca en el repo (ver `.gitignore`, `config/secrets.yaml` está excluido).
4. Uso personal/educativo — no redistribuyas los datos crudos obtenidos de portales de terceros.

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

1. Configura el portal/ciudad/rango en `config/settings.yaml`.
2. Ejecuta el scraper: `python scripts/run_pipeline.py --step scrape`
3. Limpia los datos: `python scripts/run_pipeline.py --step clean`
4. Analiza: abre los notebooks en `notebooks/` o ejecuta `python scripts/run_pipeline.py --step analyze`

## Métricas calculadas

- Precio medio y mediano por m²
- Precio por m² según nº de habitaciones y baños
- Evolución temporal del precio/m² por localización
- Comparativa entre barrios/zonas
