"""Verifica que el cálculo en Python reproduce la hoja "Dólar Real Form" del Excel original
usando los mismos insumos (los CSV semilla extraídos del Excel en oct-2026).

Los insumos de data/raw/ cambian con cada actualización y las fuentes revisan datos viejos,
así que el test usa una copia congelada de los CSV semilla (fixtures/insumos_excel/).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dolar_real.calculo import Insumos, calcular

FIX = Path(__file__).parent / "fixtures" / "excel_dolar_real_form.csv"
INSUMOS_EXCEL = Path(__file__).parent / "fixtures" / "insumos_excel"
BASE_EXCEL = pd.Timestamp("2026-09-01")

COLUMNAS = {  # columna Python -> columna Excel
    "tc_oficial_nominal": "TC $/US$ nominal ",
    "factor_inflaciones": "Factor Inflaciones",
    "oficial": "Oficial",
    "blue": "Blue",
    "banda_superior": "Banda Superior",
    "multilateral": "Multi",
    "bilateral_usa": "TCRB_USA",
    "prom_oficial": "Promedio Oficial",
    "prom_blue": "Promedio Blue",
    "prom_multilateral": "Promedio Multi",
    "brecha_twdi": "Brecha TWDI",
}


@pytest.fixture(scope="module")
def ambos():
    xl = pd.read_csv(FIX, parse_dates=["Mes"]).set_index("Mes").sort_index()
    xl = xl.apply(pd.to_numeric, errors="coerce")
    py = calcular(Insumos.desde_csv(INSUMOS_EXCEL), base=BASE_EXCEL)
    return py, xl


@pytest.mark.parametrize("py_col,xl_col", COLUMNAS.items())
def test_columna_igual_al_excel(ambos, py_col, xl_col):
    py, xl = ambos
    a = py[py_col].reindex(xl.index)
    b = xl[xl_col]
    ok = a.notna() & b.notna()
    assert ok.sum() > 0
    np.testing.assert_allclose(a[ok], b[ok], rtol=1e-6, err_msg=py_col)
