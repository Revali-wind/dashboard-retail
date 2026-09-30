import pandas as pd

RENAME = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}

REGION_KEY = ["country", "region", "state", "city", "postal_code"]
REQUIRED = ["order_id", "order_date", "ship_date", "customer_id", "product_id",
            "sales", "quantity"]


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Limpia el dataset plano. Devuelve el DataFrame y un dict con métricas de limpieza."""
    stats = {"filas_entrada": len(df)}
    df = df.rename(columns=RENAME)

    # Texto: quitar espacios y convertir vacíos en nulos
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)

    # Tipos: fechas M/D/YYYY, numéricos, código postal de 5 dígitos
    for col in ("order_date", "ship_date"):
        df[col] = pd.to_datetime(df[col], format="%m/%d/%Y", errors="coerce")
    for col in ("sales", "discount", "profit"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce").astype("Int64")
    df["postal_code"] = df["postal_code"].str.replace(r"\.0$", "", regex=True).str.zfill(5)

    # Duplicados: por Row ID y por contenido idéntico (ignorando Row ID)
    n = len(df)
    df = df.drop_duplicates(subset="row_id")
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "row_id"])
    stats["duplicados_eliminados"] = n - len(df)

    # Nulos: descartar filas sin campos esenciales; descuento nulo = sin descuento
    n = len(df)
    df = df.dropna(subset=REQUIRED)
    stats["filas_sin_campos_esenciales"] = n - len(df)
    df["discount"] = df["discount"].fillna(0.0)
    stats["profit_nulo"] = int(df["profit"].isna().sum())  # se conserva como NULL
    for col in ("segment", "ship_mode", "category", "sub_category", "product_name",
                "customer_name", "country", "region", "state", "city"):
        df[col] = df[col].fillna("Unknown")
    df["postal_code"] = df["postal_code"].fillna("00000")

    # Consistencia de fechas
    n = len(df)
    df = df[df["ship_date"] >= df["order_date"]]
    stats["envio_anterior_a_pedido"] = n - len(df)

    df["ship_days"] = (df["ship_date"] - df["order_date"]).dt.days
    stats["filas_salida"] = len(df)
    return df.reset_index(drop=True), stats


def build_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Separa el dataset plano en tablas normalizadas."""
    regiones = (df[REGION_KEY].drop_duplicates().sort_values(REGION_KEY)
                .reset_index(drop=True))
    regiones.insert(0, "region_id", regiones.index + 1)

    # Un product_id puede tener varios nombres en el origen: se queda el más frecuente
    productos = (df.groupby("product_id")
                 .agg(product_name=("product_name", lambda s: s.mode().iloc[0]),
                      category=("category", "first"),
                      sub_category=("sub_category", "first"))
                 .reset_index())

    clientes = (df.groupby("customer_id")
                .agg(customer_name=("customer_name", "first"),
                     segment=("segment", "first"))
                .reset_index())

    ventas = df.merge(regiones, on=REGION_KEY, how="left")
    ventas = ventas[["row_id", "order_id", "order_date", "ship_date", "ship_days",
                     "ship_mode", "customer_id", "product_id", "region_id",
                     "sales", "quantity", "discount", "profit"]].copy()
    for col in ("order_date", "ship_date"):
        ventas[col] = ventas[col].dt.strftime("%Y-%m-%d")

    return {"regiones": regiones, "productos": productos,
            "clientes": clientes, "ventas": ventas}
