from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "Sample - Superstore.csv"
DB_PATH = ROOT / "db" / "retail.db"
ENCODING = "latin-1"
