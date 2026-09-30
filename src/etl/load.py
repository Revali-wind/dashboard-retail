import sqlite3

import pandas as pd

from .config import DB_PATH

SCHEMA = """
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS regiones;

CREATE TABLE regiones (
    region_id   INTEGER PRIMARY KEY,
    country     TEXT NOT NULL,
    region      TEXT NOT NULL,
    state       TEXT NOT NULL,
    city        TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    UNIQUE (country, region, state, city, postal_code)
);

CREATE TABLE productos (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    sub_category TEXT NOT NULL
);

CREATE TABLE clientes (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment       TEXT NOT NULL
);

CREATE TABLE ventas (
    row_id      INTEGER PRIMARY KEY,
    order_id    TEXT NOT NULL,
    order_date  TEXT NOT NULL,          -- ISO YYYY-MM-DD
    ship_date   TEXT NOT NULL,
    ship_days   INTEGER NOT NULL,
    ship_mode   TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES clientes (customer_id),
    product_id  TEXT NOT NULL REFERENCES productos (product_id),
    region_id   INTEGER NOT NULL REFERENCES regiones (region_id),
    sales       REAL NOT NULL,
    quantity    INTEGER NOT NULL,
    discount    REAL NOT NULL,
    profit      REAL
);

CREATE INDEX idx_ventas_order_date ON ventas (order_date);
CREATE INDEX idx_ventas_customer   ON ventas (customer_id);
CREATE INDEX idx_ventas_product    ON ventas (product_id);
CREATE INDEX idx_ventas_region     ON ventas (region_id);
"""

# Orden de carga: primero dimensiones, luego hechos
LOAD_ORDER = ["regiones", "productos", "clientes", "ventas"]


def load(tables: dict[str, pd.DataFrame], db_path=DB_PATH) -> dict[str, int]:
    """Recrea el esquema y carga las tablas. Devuelve los registros por tabla según la BD."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        for name in LOAD_ORDER:
            tables[name].to_sql(name, conn, if_exists="append", index=False)
        conn.commit()
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Violaciones de clave foránea: {len(violations)}")
        return {n: conn.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]
                for n in LOAD_ORDER}
