# 📊 Dashboard de Ventas Retail

## Sobre el proyecto

Pipeline ETL y dashboard interactivo construido con Python para analizar 4 años de ventas retail (9.993 registros). Permite explorar KPIs de ventas, profit y márgenes por categoría, región y período de tiempo, con filtros dinámicos en tiempo real. Desarrollado como proyecto de portfolio para demostrar habilidades en análisis de datos, transformación ETL y visualización interactiva.

Proyecto de análisis de datos de punta a punta sobre el dataset **Sample - Superstore**: un pipeline ETL que limpia y normaliza los datos, una base SQLite y un dashboard interactivo para explorar ventas, rentabilidad y desempeño geográfico.

## Stack técnico

| Capa | Tecnología |
|---|---|
| ETL | Python 3.9+, pandas |
| Almacenamiento | SQLite (`sqlite3`, incluido en Python) |
| Dashboard | Streamlit |
| Visualización | Plotly (matplotlib disponible para exploración en notebooks) |

## Estructura

```
dashboard-retail/
├── app/streamlit_app.py     # Dashboard interactivo
├── src/etl/
│   ├── config.py            # Rutas y encoding
│   ├── extract.py           # Lectura del CSV (latin-1)
│   ├── transform.py         # Limpieza y normalización
│   ├── load.py              # Esquema SQLite y carga
│   └── pipeline.py          # Orquestador del ETL
├── data/raw/                # CSV original (no versionado)
├── db/                      # Base retail.db generada (no versionada)
├── notebooks/               # Exploración
└── requirements.txt
```

## Instalación

```bash
git clone <url-del-repositorio>
cd dashboard-retail

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Datos

Descarga **Sample - Superstore** desde Kaggle y colócalo en `data/raw/` con el nombre `Sample - Superstore.csv`. El CSV no se incluye en el repositorio.

## Ejecución

**1. Ejecutar el ETL** (crea `db/retail.db`; se puede repetir, recrea la base desde cero):

```bash
python -m src.etl.pipeline
```

**2. Lanzar el dashboard:**

```bash
streamlit run app/streamlit_app.py
```

Se abrirá en `http://localhost:8501`.

## Pipeline ETL

- **Extracción:** lectura del CSV con encoding `latin-1`; el código postal se lee como texto para conservar los ceros iniciales.
- **Limpieza:** fechas convertidas a formato ISO, eliminación de duplicados, manejo de nulos, validación de que el envío no sea anterior al pedido y columna derivada `ship_days`.
- **Modelo:** esquema normalizado con claves foráneas e índices.

| Tabla | Contenido | Registros |
|---|---|---|
| `ventas` | Líneas de pedido (hechos) | 9.993 |
| `productos` | Producto, categoría y subcategoría | 1.862 |
| `clientes` | Cliente y segmento | 793 |
| `regiones` | País, región, estado, ciudad y código postal | 632 |

## Dashboard

- **Filtros** (barra lateral): rango de fechas, categoría de producto y región. Afectan a todos los gráficos.
- **KPIs:** ventas totales, profit total, número de pedidos y margen promedio (profit / ventas).
- **Gráficos:** ventas por mes, ventas y profit por categoría, top 10 de productos y ventas por estado (mapa y tabla).

## Key insights

1. **Los descuentos superiores al 20 % destruyen rentabilidad.** Las líneas sin descuento tienen un margen del 29,5 %. Entre 20 % y 40 % el margen es de −15,3 %, y por encima del 40 % cae a −77,4 %. Solo ese segmento suma 362 mil USD en ventas y −135 mil USD de profit.
2. **Furniture vende mucho pero deja casi nada.** Es la segunda categoría en ventas (742 mil USD) pero su margen es del 2,5 %, frente al 17 % de Office Supplies y Technology. La causa son *Tables* (−17,7 mil USD de profit, margen −8,6 %) y *Bookcases* (−3,5 mil USD).
3. **Fuerte estacionalidad y crecimiento sostenido.** Entre septiembre y diciembre se concentra el 52 % de las ventas anuales, y las ventas de 2017 (733 mil USD) superan en un 51 % a las de 2014 (484 mil USD).

> Cifras calculadas sobre las 9.993 líneas de venta cargadas tras la limpieza (2014–2017).
