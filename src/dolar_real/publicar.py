"""Genera las salidas publicadas en docs/ (GitHub Pages):

- docs/data.json       datos para la página web
- docs/dolar_real.csv  serie completa, la lee la consulta Power Query del Excel de clase
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import pandas as pd

from .calculo import ROOT, Insumos, calcular, resumen

DOCS = ROOT / "docs"
EVENTOS = ROOT / "config" / "eventos.csv"

SERIES_WEB = {  # columna -> clave en data.json
    "oficial": "oficial",
    "blue": "blue",
    "multilateral": "multilateral",
    "bilateral_usa": "bilateral_usa",
    "banda_inferior": "banda_inferior",
    "banda_superior": "banda_superior",
    "prom_oficial": "prom_oficial",
    "prom_blue": "prom_blue",
    "prom_multilateral": "prom_multilateral",
    "prom_oficial_aj_twdi": "prom_oficial_aj_twdi",
    "prom_blue_aj_twdi": "prom_blue_aj_twdi",
    "tc_oficial_nominal": "oficial_nominal",
    "tc_blue_nominal": "blue_nominal",
}


def _lista(s: pd.Series):
    return [None if (v is None or (isinstance(v, float) and math.isnan(v))) else round(float(v), 2)
            for v in s]


def publicar() -> dict:
    ins = Insumos.desde_csv()
    df = calcular(ins)
    res = resumen(df)
    # En la web el blue se muestra sólo en los meses en que existió (en el cálculo se usa el oficial)
    hay_blue = ins.blue.reindex(df.index).notna()
    web = df.copy()
    for c in ("blue", "tc_blue_nominal"):
        web[c] = web[c].where(hay_blue)
    DOCS.mkdir(exist_ok=True)

    ev = pd.read_csv(EVENTOS, parse_dates=["mes"])
    ev = ev[ev["mes"] <= df.index.max()]
    data = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "resumen": res,
        "meses": [d.strftime("%Y-%m") for d in df.index],
        "series": {k: _lista(web[c]) for c, k in SERIES_WEB.items()},
        "eventos": [{"mes": r.mes.strftime("%Y-%m"), "evento": r.evento, "serie": r.serie}
                    for r in ev.itertuples()],
    }
    (DOCS / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                                    encoding="utf-8")

    out = df.copy()
    out.index = out.index.strftime("%Y-%m-%d")
    out.to_csv(DOCS / "dolar_real.csv", float_format="%.10g", lineterminator="\n")
    return res


if __name__ == "__main__":
    print(publicar()["mes_base"])
