"""Tests de los parsers auxiliares (no requieren red)."""
import pandas as pd

from dolar_real.fuentes import _fecha_es, _num_ar


def test_num_ar():
    assert _num_ar("1.550,25") == 1550.25
    assert _num_ar("1.550") == 1550.0
    assert _num_ar("346,5") == 346.5
    assert _num_ar("346.5") == 346.5
    assert _num_ar(12) == 12.0


def test_fecha_es():
    assert _fecha_es("ene-17") == pd.Timestamp("2017-01-01")
    assert _fecha_es("Septiembre 2026") == pd.Timestamp("2026-09-01")
    assert _fecha_es(pd.Timestamp("2024-03-01")) == pd.Timestamp("2024-03-01")
    assert _fecha_es(pd.Timestamp("2026-03-26")) == pd.Timestamp("2026-03-01")
