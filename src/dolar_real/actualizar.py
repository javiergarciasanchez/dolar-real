"""Actualización mensual: descarga fuentes → valida → guarda CSV → recalcula → publica.

    python -m dolar_real.actualizar            # descarga todo y regenera salidas
    python -m dolar_real.actualizar --offline  # sólo recalcula con los CSV existentes

Si alguna fuente falla o no pasa las validaciones, se conserva su CSV anterior,
se registra el problema en data/estado.json y el proceso termina con código 1
(en GitHub Actions eso dispara un mail de aviso). Las salidas se regeneran igual,
con el mes base que permitan los datos disponibles.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone

import pandas as pd

from . import fuentes as F
from .calculo import RAW, ROOT
from .publicar import publicar

ESTADO = ROOT / "data" / "estado.json"


class ErrorValidacion(Exception):
    pass


def _leer(nombre):
    return pd.read_csv(RAW / nombre, parse_dates=[0])


def _guardar(df, nombre):
    df = df.sort_values(df.columns[0]).reset_index(drop=True).copy()
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0]).dt.strftime("%Y-%m-%d")
    df.to_csv(RAW / nombre, index=False, float_format="%.10g")


def _validar(viejo: pd.DataFrame, nuevo: pd.DataFrame, col: str, *, rango, salto_max,
             revision_max=0.05, mensual=True, desde=None) -> list[str]:
    """Controles de cordura. Lanza ErrorValidacion si algo es grave; devuelve avisos."""
    avisos = []
    if nuevo.empty:
        raise ErrorValidacion("la descarga vino vacía")
    f = nuevo.columns[0]
    n = nuevo.set_index(pd.to_datetime(nuevo[f]))[col].sort_index()
    v = viejo.set_index(pd.to_datetime(viejo[f]))[col].sort_index()
    if n.index.max() < v.index.max():
        raise ErrorValidacion(f"el último dato ({n.index.max():%Y-%m}) es anterior al que ya había ({v.index.max():%Y-%m})")
    if n.index.duplicated().any():
        raise ErrorValidacion("hay fechas duplicadas")
    if desde is not None:   # los controles de rango/saltos/huecos sólo sobre el tramo descargado
        n = n[n.index >= desde]
    fuera = n[(n < rango[0]) | (n > rango[1])]
    if len(fuera):
        raise ErrorValidacion(f"valores fuera de rango {rango}: {fuera.head(3).to_dict()}")
    if mensual:
        esperado = pd.date_range(n.index.min(), n.index.max(), freq="MS")
        faltan = esperado.difference(n.index)
        if len(faltan):
            avisos.append(f"meses faltantes: {[d.strftime('%Y-%m') for d in faltan[:6]]}")
    if salto_max is not None:
        saltos = n.pct_change().abs() if col != "inflacion" else n.diff().abs()
        grandes = saltos[saltos > salto_max]
        if len(grandes):
            avisos.append(f"saltos grandes: {[d.strftime('%Y-%m') for d in grandes.index[:6]]}")
    comun = n.index.intersection(v.index)
    if len(comun):
        rev = (n[comun] / v[comun] - 1).abs() if col != "inflacion" else (n[comun] - v[comun]).abs()
        revisados = rev[rev > revision_max]
        if len(revisados):
            avisos.append(f"{len(revisados)} meses revisados >{revision_max:.0%} (ej. {revisados.index[0]:%Y-%m})")
    return avisos


def _empalmar(viejo: pd.DataFrame, nuevo: pd.DataFrame, desde) -> pd.DataFrame:
    f = viejo.columns[0]
    v = viejo[pd.to_datetime(viejo[f]) < desde]
    n = nuevo[pd.to_datetime(nuevo[f]) >= desde]
    return pd.concat([v, n[viejo.columns]], ignore_index=True)


def _paso(estado, nombre, archivo, col, obtener, *, desde=None, **val):
    print(f"· {nombre}")
    viejo = _leer(archivo)
    try:
        nuevo = obtener()
        if desde is not None:
            nuevo = _empalmar(viejo, nuevo, desde)
        avisos = _validar(viejo, nuevo, col, desde=desde, **val)
        _guardar(nuevo, archivo)
        ult = pd.to_datetime(nuevo.iloc[:, 0]).max()
        estado[nombre] = {"ok": True, "ultimo_mes": ult.strftime("%Y-%m"), "avisos": avisos}
        print(f"  ok, último dato {ult:%Y-%m}" + (f"  avisos: {avisos}" if avisos else ""))
    except Exception as e:  # noqa: BLE001
        ult = pd.to_datetime(viejo.iloc[:, 0]).max()
        estado[nombre] = {"ok": False, "ultimo_mes": ult.strftime("%Y-%m"), "error": str(e)}
        print(f"  ERROR: {e}")
        traceback.print_exc()


def descargar() -> dict:
    est: dict = {}
    _paso(est, "Tipo de cambio oficial (BCRA Com. A 3500)", "tc_oficial_mensual.csv", "tc_oficial",
          F.tc_oficial_bcra, desde=F.DESDE_COM3500, rango=(1e-14, 1e6), salto_max=0.6)

    def _blue():
        act = F.blue_diario()
        _guardar(act, "blue_diario_desde_2023.csv")
        hist = pd.read_csv(RAW / "blue_diario_ambito_hasta_2022.csv")
        return F.blue_mensual(hist, act)
    _paso(est, "Dólar blue (Ámbito)", "blue_mensual.csv", "blue", _blue,
          desde=F.DESDE_BLUE_ACTUAL, rango=(1, 1e6), salto_max=0.6, mensual=False)

    _paso(est, "Inflación Argentina (INDEC)", "inflacion_argentina_mensual.csv", "inflacion",
          F.inflacion_indec, desde=F.DESDE_IPC_NACIONAL, rango=(-0.05, 0.5), salto_max=0.1,
          revision_max=0.002)
    _paso(est, "CPI Estados Unidos (FRED)", "cpi_usa_mensual.csv", "cpi", F.cpi_usa,
          rango=(1, 2000), salto_max=0.03, revision_max=0.01)
    _paso(est, "ITCRM (BCRA)", "itcrm_bcra_normalizado.csv", "itcrm_norm", F.itcrm,
          rango=(0.05, 20), salto_max=0.5, revision_max=10)   # renormaliza: revisiones esperables
    hist_twdi = _leer("twdi_fred_mensual.csv")
    _paso(est, "Índice real del dólar (FRED)", "twdi_fred_mensual.csv", "twdi",
          lambda: F.twdi(hist_twdi), rango=(50, 200), salto_max=0.1, revision_max=0.03,
          desde=F.INICIO_RTWEXBGS)
    _paso(est, "Bandas cambiarias (BCRA)", "bandas_cambiarias_mensual.csv", "banda_superior",
          F.bandas, desde=F.DESDE_BANDAS_2026, rango=(1, 1e6), salto_max=0.2, mensual=False)
    return est


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="no descargar; sólo recalcular")
    a = ap.parse_args(argv)

    estado = {} if a.offline else descargar()
    info = publicar()
    salida = {"actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
              "mes_base": info["mes_base"], "fuentes": estado}
    ESTADO.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    fallas = [k for k, v in estado.items() if not v["ok"]]
    print(f"\nMes base: {info['mes_base']}")
    if fallas:
        print(f"Fuentes con error: {fallas}")
        sys.exit(1)


if __name__ == "__main__":
    main()
