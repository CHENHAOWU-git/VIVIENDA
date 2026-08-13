import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.clean import clean_listings


def test_clean_listings_calculates_precio_m2_and_drops_invalid_rows():
    df = pd.DataFrame({
        "fecha_publicacion": ["2024-01-15", "2024-02-01", "2024-02-10"],
        "precio": [200000, None, 150000],
        "superficie_m2": [80, 60, 0],
        "habitaciones": [2, 3, 1],
        "banos": [1, 2, 1],
        "ciudad": ["Madrid", "Madrid", "Barcelona"],
        "zona": ["Chamberí", "Salamanca", "Eixample"],
        "direccion": ["a", "b", "c"],
        "tipo_inmueble": ["piso", "piso", "piso"],
        "url": ["http://x/1", "http://x/2", "http://x/3"],
    })

    result = clean_listings(df)

    assert len(result) == 1
    assert result.loc[0, "precio_m2"] == 2500.0


def test_clean_listings_drops_duplicate_urls():
    df = pd.DataFrame({
        "fecha_publicacion": ["2024-01-15", "2024-01-15"],
        "precio": [200000, 200000],
        "superficie_m2": [80, 80],
        "habitaciones": [2, 2],
        "banos": [1, 1],
        "ciudad": ["Madrid", "Madrid"],
        "zona": ["Chamberí", "Chamberí"],
        "direccion": ["a", "a"],
        "tipo_inmueble": ["piso", "piso"],
        "url": ["http://x/1", "http://x/1"],
    })

    result = clean_listings(df)

    assert len(result) == 1
