"""Cálculo del tipo de cambio real de Argentina.

Replica la hoja "Dólar Real Form" del Excel original:

    TCR(m) = TC nominal(m) × Π_{k = m+1 .. base} (1 + π_ARG,k) / (1 + π_USA,k)

El mes base es el último mes con inflación publicada en ambos países (y tipo de cambio).
En el mes base el valor real coincide con el nominal; los meses anteriores quedan
expresados en pesos del mes base, ajustados por inflación relativa Argentina/USA.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INICIO = pd.Timestamp("1970-01-01")


def _leer(nombre: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / nombre, parse_dates=["mes"])
    return df.set_index("mes").sort_index()


@dataclass
class Insumos:
    tc_oficial: pd.Series
    blue: pd.Series
    inflacion_arg: pd.Series
    cpi_usa: pd.Series
    itcrm: pd.DataFrame          # columnas itcrm_norm, itcrb_usa_norm
    twdi: pd.Series
    bandas: pd.DataFrame         # columnas banda_inferior, banda_superior

    @classmethod
    def desde_csv(cls) -> "Insumos":
        return cls(
            tc_oficial=_leer("tc_oficial_mensual.csv")["tc_oficial"],
            blue=_leer("blue_mensual.csv")["blue"],
            inflacion_arg=_leer("inflacion_argentina_mensual.csv")["inflacion"],
            cpi_usa=_leer("cpi_usa_mensual.csv")["cpi"],
            itcrm=_leer("itcrm_bcra_normalizado.csv"),
            twdi=_leer("twdi_fred_mensual.csv")["twdi"],
            bandas=_leer("bandas_cambiarias_mensual.csv"),
        )


def mes_base(ins: Insumos) -> pd.Timestamp:
    """Último mes con datos de inflación de ambos países y tipo de cambio oficial."""
    return min(ins.inflacion_arg.dropna().index.max(),
               ins.cpi_usa.dropna().index.max(),
               ins.tc_oficial.dropna().index.max())


def calcular(ins: Insumos, base: pd.Timestamp | None = None) -> pd.DataFrame:
    base = base or mes_base(ins)
    meses = pd.date_range(INICIO, base, freq="MS")
    df = pd.DataFrame(index=pd.Index(meses, name="mes"))

    df["tc_oficial_nominal"] = ins.tc_oficial.reindex(meses)
    blue = ins.blue.reindex(meses)
    # Donde no hay blue (cepo inexistente) se usa el oficial, como en el Excel
    df["tc_blue_nominal"] = blue.where(blue.notna() & (blue != 0), df["tc_oficial_nominal"])
    df["banda_inferior_nominal"] = ins.bandas["banda_inferior"].reindex(meses)
    df["banda_superior_nominal"] = ins.bandas["banda_superior"].reindex(meses)

    df["inflacion_arg"] = ins.inflacion_arg.reindex(meses).fillna(0.0)
    # Meses sin CPI publicado (p.ej. oct-2025, cierre del gobierno de EE.UU.) se interpolan
    cpi = ins.cpi_usa.sort_index()
    cpi = cpi.reindex(pd.date_range(cpi.index.min(), cpi.index.max(), freq="MS")).interpolate()
    infl_usa = cpi.pct_change()
    df["inflacion_usa"] = infl_usa.reindex(meses).fillna(0.0)

    # Factor de inflaciones: producto acumulado de (1+πA)/(1+πU) de los meses POSTERIORES
    rel = (1 + df["inflacion_arg"]) / (1 + df["inflacion_usa"])
    df["factor_inflaciones"] = rel[::-1].cumprod()[::-1].shift(-1).fillna(1.0)

    k = df["factor_inflaciones"]
    df["oficial"] = df["tc_oficial_nominal"] * k
    df["blue"] = df["tc_blue_nominal"] * k
    df["banda_inferior"] = df["banda_inferior_nominal"] * k
    df["banda_superior"] = df["banda_superior_nominal"] * k

    # ITCRM y bilateral USA del BCRA, reescalados para que el mes base valga el TC oficial nominal
    tc_base = df.loc[base, "tc_oficial_nominal"]
    itc = ins.itcrm.reindex(meses)
    if base in ins.itcrm.index:
        itc = itc / ins.itcrm.loc[base]          # renormaliza si la serie trae meses posteriores
    df["multilateral"] = itc["itcrm_norm"] * tc_base
    df["bilateral_usa"] = itc["itcrb_usa_norm"] * tc_base

    # Promedios históricos (en pesos del mes base)
    df["prom_multilateral"] = df["multilateral"].mean()
    df["prom_oficial"] = df["oficial"].mean()
    df["prom_blue"] = df["blue"].mean()

    # Ajuste por fortaleza global del dólar (TWDI real vs. su promedio histórico)
    brecha = ins.twdi / ins.twdi.mean() - 1
    df["brecha_twdi"] = brecha.reindex(meses).fillna(0.0)
    df["prom_oficial_aj_twdi"] = df["prom_oficial"] * (1 + df["brecha_twdi"])
    df["prom_blue_aj_twdi"] = df["prom_blue"] * (1 + df["brecha_twdi"])

    # Promedios expresados en moneda corriente de cada mes
    df["prom_oficial_corriente"] = df["prom_oficial"] / k
    df["prom_blue_corriente"] = df["prom_blue"] / k
    return df


def resumen(df: pd.DataFrame) -> dict:
    """Indicadores del mes base (equivalente al bloque superior de la hoja del Excel)."""
    base = df.index.max()
    u = df.loc[base]
    b = u["brecha_twdi"]
    promedios = {
        "Promedio oficial": u["prom_oficial"],
        "Promedio multilateral": u["prom_multilateral"],
        "Promedio oficial ajustado por TWDI": u["prom_oficial"] * (1 + b),
        "Promedio multilateral ajustado por TWDI": u["prom_multilateral"] * (1 + b),
        "Promedio blue": u["prom_blue"],
        "Promedio blue ajustado por TWDI": u["prom_blue"] * (1 + b),
    }
    actuales = {"Oficial": u["tc_oficial_nominal"], "Blue": u["tc_blue_nominal"],
                "Banda superior": u["banda_superior_nominal"]}
    desvios = {a: {p: (va / vp - 1) for p, vp in promedios.items()}
               for a, va in actuales.items() if pd.notna(va)}
    return {
        "mes_base": base.strftime("%Y-%m"),
        "actuales": {k: float(v) for k, v in actuales.items() if pd.notna(v)},
        "brecha_blue_oficial": float(u["tc_blue_nominal"] / u["tc_oficial_nominal"] - 1),
        "promedios": {k: float(v) for k, v in promedios.items()},
        "desvios": desvios,
        "primer_mes": df.index.min().strftime("%Y-%m"),
    }


if __name__ == "__main__":
    d = calcular(Insumos.desde_csv())
    print(d.tail(3).T)
    print(resumen(d))
