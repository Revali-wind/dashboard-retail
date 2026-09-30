import pandas as pd

from .config import ENCODING, RAW_CSV


def extract(path=RAW_CSV) -> pd.DataFrame:
    """Lee el CSV crudo. Postal Code se lee como texto para no perder ceros a la izquierda."""
    return pd.read_csv(path, encoding=ENCODING, dtype={"Postal Code": "string"})
