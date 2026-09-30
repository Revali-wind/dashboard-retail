"""Dashboard de ventas retail. Ejecutar: streamlit run app/streamlit_app.py"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Permite importar `src` al ejecutar con `streamlit run app/streamlit_app.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.etl.config import DB_PATH, RAW_CSV  # noqa: E402
from src.etl.pipeline import run as run_etl  # noqa: E402

# Paleta categórica fija: cada medida conserva su color en todos los gráficos
C_SALES, C_PROFIT = "#2a78d6", "#eb6834"
SEQ_BLUE = ["#dbe9fa", "#8db8ec", "#2a78d6", "#123f7a"]

US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

QUERY = """
SELECT v.order_id, v.order_date, v.sales, v.profit, v.quantity,
       p.product_name, p.category, p.sub_category,
       r.region, r.state
FROM ventas v
JOIN productos p USING (product_id)
JOIN regiones  r USING (region_id)
"""

st.set_page_config(page_title="Dashboard Retail", page_icon="📊", layout="wide")


@st.cache_resource(show_spinner="Generando la base de datos (primer arranque)…")
def ensure_db() -> None:
    """Si retail.db no existe (p. ej. en Streamlit Cloud), ejecuta el ETL para crearla."""
    if DB_PATH.exists():
        return
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"No se encontró el CSV de origen: {RAW_CSV}")
    try:
        run_etl()
    except Exception:
        DB_PATH.unlink(missing_ok=True)  # evita dejar una base a medias
        raise


@st.cache_data(show_spinner="Cargando datos…")
def load_data() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(QUERY, conn, parse_dates=["order_date"])
    return df


def money(x: float) -> str:
    return f"${x:,.0f}"


def style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=8, b=8),
                      legend=dict(orientation="h", y=1.1, x=0, title=None))
    return fig


try:
    ensure_db()
except Exception as exc:
    st.error(f"No se pudo generar {DB_PATH.name} con el ETL: {exc}")
    st.stop()

data = load_data()

# ---------------------------------------------------------------- Sidebar
st.sidebar.header("Filtros")
dmin, dmax = data["order_date"].min().date(), data["order_date"].max().date()
date_range = st.sidebar.date_input("Rango de fechas", (dmin, dmax),
                                   min_value=dmin, max_value=dmax)
categories = sorted(data["category"].unique())
sel_cat = st.sidebar.multiselect("Categoría de producto", categories, default=categories)
regions = sorted(data["region"].unique())
sel_reg = st.sidebar.multiselect("Región", regions, default=regions)

# date_input devuelve 1 fecha mientras el usuario aún elige el fin del rango
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
else:
    start = end = date_range[0] if isinstance(date_range, (tuple, list)) else date_range

df = data[
    data["order_date"].between(pd.Timestamp(start), pd.Timestamp(end))
    & data["category"].isin(sel_cat)
    & data["region"].isin(sel_reg)
]

st.title("📊 Dashboard de ventas retail")
st.caption(f"{start:%d/%m/%Y} – {end:%d/%m/%Y} · {len(df):,} líneas de venta")

if df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ------------------------------------------------------------------- KPIs
total_sales, total_profit = df["sales"].sum(), df["profit"].sum()
margin = total_profit / total_sales if total_sales else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Ventas totales", money(total_sales))
k2.metric("Profit total", money(total_profit))
k3.metric("Número de pedidos", f"{df['order_id'].nunique():,}")
k4.metric("Margen promedio", f"{margin:.1%}",
          help="Profit total / Ventas totales (ponderado por ventas)")

# ------------------------------------------------- Ventas por mes (línea)
st.subheader("Ventas por mes")
monthly = (df.groupby(df["order_date"].dt.to_period("M").dt.to_timestamp())["sales"]
           .sum().reset_index())
fig = px.line(monthly, x="order_date", y="sales", markers=True,
              color_discrete_sequence=[C_SALES],
              labels={"order_date": "", "sales": "Ventas ($)"})
fig.update_traces(line_width=2, marker_size=6,
                  hovertemplate="%{x|%b %Y}<br>Ventas: $%{y:,.0f}<extra></extra>")
fig.update_yaxes(tickprefix="$", rangemode="tozero")
st.plotly_chart(style(fig))

# ------------------------- Categoría (barras) y Top 10 productos (barras h)
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Ventas y profit por categoría")
    cat = (df.groupby("category")[["sales", "profit"]].sum().reset_index()
           .melt("category", var_name="medida", value_name="valor"))
    cat["medida"] = cat["medida"].map({"sales": "Ventas", "profit": "Profit"})
    fig = px.bar(cat, x="category", y="valor", color="medida", barmode="group",
                 color_discrete_map={"Ventas": C_SALES, "Profit": C_PROFIT},
                 category_orders={"medida": ["Ventas", "Profit"]},
                 labels={"category": "", "valor": "USD", "medida": ""})
    fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}<extra></extra>")
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(style(fig))

with col_b:
    st.subheader("Top 10 productos por ventas")
    top = (df.groupby("product_name")["sales"].sum().nlargest(10)
           .sort_values().reset_index())
    top["label"] = top["product_name"].where(top["product_name"].str.len() <= 40,
                                             top["product_name"].str.slice(0, 39) + "…")
    fig = px.bar(top, y="label", x="sales", orientation="h",
                 color_discrete_sequence=[C_SALES], custom_data=["product_name"],
                 labels={"label": "", "sales": "Ventas ($)"})
    fig.update_traces(hovertemplate="%{customdata[0]}<br>Ventas: $%{x:,.0f}<extra></extra>")
    fig.update_xaxes(tickprefix="$")
    st.plotly_chart(style(fig))

# ------------------------------------------------- Ventas por estado
st.subheader("Ventas por estado")
states = (df.groupby("state").agg(ventas=("sales", "sum"), profit=("profit", "sum"),
                                  pedidos=("order_id", "nunique")).reset_index())
states["margen"] = states["profit"] / states["ventas"]
states["code"] = states["state"].map(US_STATES)

tab_map, tab_table = st.tabs(["Mapa", "Tabla"])
with tab_map:
    fig = px.choropleth(states, locations="code", locationmode="USA-states",
                        color="ventas", scope="usa", hover_name="state",
                        hover_data={"code": False, "ventas": ":$,.0f",
                                    "profit": ":$,.0f", "pedidos": ":,"},
                        color_continuous_scale=SEQ_BLUE,
                        labels={"ventas": "Ventas", "profit": "Profit"})
    fig.update_layout(coloraxis_colorbar=dict(title="Ventas", tickprefix="$"))
    fig.update_geos(bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(style(fig, 460))
with tab_table:
    st.dataframe(
        states.drop(columns="code").sort_values("ventas", ascending=False),
        hide_index=True, width="stretch",
        column_config={
            "state": "Estado",
            "ventas": st.column_config.NumberColumn("Ventas", format="$%,.0f"),
            "profit": st.column_config.NumberColumn("Profit", format="$%,.0f"),
            "pedidos": st.column_config.NumberColumn("Pedidos", format="%d"),
            "margen": st.column_config.NumberColumn("Margen", format="percent"),
        },
    )
