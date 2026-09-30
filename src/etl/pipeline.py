"""Ejecuta el ETL completo: python -m src.etl.pipeline"""
from .config import DB_PATH
from .extract import extract
from .load import load
from .transform import build_tables, clean


def run() -> None:
    raw = extract()
    df, stats = clean(raw)
    counts = load(build_tables(df))

    print("=== Limpieza ===")
    for k, v in stats.items():
        print(f"  {k:<30}{v:>8,}")
    print(f"\n=== Registros cargados en {DB_PATH.name} ===")
    for table, n in counts.items():
        print(f"  {table:<30}{n:>8,}")


if __name__ == "__main__":
    run()
