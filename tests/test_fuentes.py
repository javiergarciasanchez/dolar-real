"""Tests de los parsers auxiliares (no requieren red)."""
import pandas as pd

from dolar_real.fuentes import _fecha_es, _num_ar, agregar_ipc


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


def test_agregar_ipc():
    d = pd.DataFrame({"mes": pd.to_datetime(["2017-01-01", "2016-11-01", "2016-12-01"]),
                      "inflacion": [0.10, 0.05, 0.25]})
    ipc = agregar_ipc(d).set_index("mes")["ipc"]
    assert ipc["2016-12-01"] == 100
    assert abs(ipc["2017-01-01"] - 110) < 1e-9
    assert abs(ipc["2016-11-01"] - 80) < 1e-9
