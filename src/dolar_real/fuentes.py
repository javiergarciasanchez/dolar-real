"""Descarga de las fuentes de datos (port de las consultas Power Query del Excel original).

Cada función devuelve un DataFrame con el mismo esquema que su CSV en data/raw/.
La documentación de cada fuente está en FUENTES.md.

ESTADO: escrito en oct-2026 sin acceso de red a las fuentes. La primera corrida real
(en la PC o en GitHub Actions) tiene que verificar cada función; ver CLAUDE.md.
"""
from __future__ import annotations

import io
import re
import time

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (dolar-real; jgsanchez@iae.edu.ar)"}
TIMEOUT = 90


def _get(url: str, intentos: int = 3, **kw) -> requests.Response:
    ultimo = None
    for i in range(intentos):
        try:
            r = requests.get(url, headers=UA, timeout=TIMEOUT, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException as e:   # noqa: PERF203
            ultimo = e
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo}")


def _mes(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


def _num_ar(x) -> float:
    """Convierte '1.550,25' / '1.550' / '346,5' / 346.5 a float."""
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    return float(s)


def _buscar_fila(df: pd.DataFrame, texto: str) -> int:
    """Índice de la primera fila que contiene una celda que empieza con `texto`."""
    for i, fila in df.iterrows():
        if any(isinstance(v, str) and v.strip().lower().startswith(texto.lower()) for v in fila):
            return i
    raise ValueError(f"No encontré una fila con '{texto}'")


# ---------------------------------------------------------------- Tipo de cambio oficial
URL_COM3500 = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/com3500.xls"
DESDE_COM3500 = pd.Timestamp("2019-11-01")


def tc_oficial_bcra() -> pd.DataFrame:
    """Promedio mensual del TC de referencia Com. A 3500 (mayorista), desde nov-2019."""
    contenido = _get(URL_COM3500).content
    hojas = pd.read_excel(io.BytesIO(contenido), sheet_name=None, header=None)
    hoja = next((h for n, h in hojas.items() if "TCR diario" in n), None)
    if hoja is None:
        raise ValueError(f"com3500.xls: no está la hoja 'TCR diario y TCNPM' (hojas: {list(hojas)})")
    h = _buscar_fila(hoja, "Fecha")
    enc = [str(v).strip() for v in hoja.iloc[h]]
    c_fecha = enc.index("Fecha")
    c_tc = next(i for i, v in enumerate(enc) if v.startswith("Tipo de Cambio de Referencia"))
    d = hoja.iloc[h + 1:, [c_fecha, c_tc]].copy()
    d.columns = ["fecha", "tc"]
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    d["tc"] = pd.to_numeric(d["tc"], errors="coerce")
    d = d.dropna()
    d = d[d["fecha"] >= DESDE_COM3500]
    m = d.groupby(_mes(d["fecha"]))["tc"].mean().rename("tc_oficial").rename_axis("mes").reset_index()
    return m


# ---------------------------------------------------------------- Dólar blue
URL_AMBITO = "https://mercados.ambito.com/dolar/informal/historico-general/01-01-2023/01-01-2100"
URL_ARGENTINADATOS = "https://api.argentinadatos.com/v1/cotizaciones/dolares/blue"
DESDE_BLUE_ACTUAL = pd.Timestamp("2023-01-01")


def blue_diario() -> pd.DataFrame:
    """Cotización diaria del blue desde 2023 (Ámbito; si falla, ArgentinaDatos)."""
    try:
        filas = _get(URL_AMBITO).json()
        enc, datos = filas[0], filas[1:]
        d = pd.DataFrame(datos, columns=[str(c).strip().lower() for c in enc])
        # Ámbito devuelve "23/10/2026". Algunos días vienen repetidos (a veces con valores
        # distintos); se conservan porque así los promediaba el Excel original.
        d["fecha"] = pd.to_datetime(d["fecha"].str.replace("-", "/"), format="%d/%m/%Y",
                                    errors="coerce")
        fuente = "ambito"
    except Exception as e:  # noqa: BLE001
        print(f"  Ámbito falló ({e}); uso ArgentinaDatos")
        d = pd.DataFrame(_get(URL_ARGENTINADATOS).json())
        d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
        fuente = "argentinadatos"
    for c in ("compra", "venta"):
        d[c] = d[c].map(_num_ar)
    d = d.dropna(subset=["fecha", "venta"])
    d = d[d["fecha"] >= DESDE_BLUE_ACTUAL][["fecha", "compra", "venta"]]
    d.attrs["fuente"] = fuente
    return d.sort_values("fecha")


def blue_mensual(diario_hist: pd.DataFrame, diario_act: pd.DataFrame) -> pd.DataFrame:
    """Promedio mensual de la venta. Sólo períodos con cepo (2011-2015 y desde ago-2019)."""
    d = pd.concat([diario_hist, diario_act])
    d["fecha"] = pd.to_datetime(d["fecha"])
    m = d.groupby(_mes(d["fecha"]))["venta"].mean().rename("blue").rename_axis("mes")
    m = m[((m.index >= "2011-01-01") & (m.index <= "2015-12-01")) | (m.index >= "2019-08-01")]
    return m.reset_index()


# ---------------------------------------------------------------- Inflación Argentina
URL_INDEC_IPC = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_divisiones.xls"
URL_DATOSGOB_IPC = ("https://apis.datos.gob.ar/series/api/series?ids=145.3_INGNACNAL_DICI_M_15"
                    "&representation_mode=percent_change&limit=1000&format=csv")
DESDE_IPC_NACIONAL = pd.Timestamp("2017-01-01")
MESES_ES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
            "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}


def _fecha_es(v):
    if isinstance(v, (pd.Timestamp,)) or hasattr(v, "year"):
        return pd.Timestamp(v).to_period("M").to_timestamp()   # INDEC tiene "26/03/2026" en mar-26
    s = str(v).strip().lower()
    m = re.match(r"([a-z]{3})[a-z]*[-\s/]*(\d{2,4})", s)
    if not m:
        return pd.NaT
    a = int(m.group(2))
    return pd.Timestamp(a + 2000 if a < 100 else a, MESES_ES[m.group(1)], 1)


def inflacion_indec() -> pd.DataFrame:
    """Variación mensual del IPC Nacional (INDEC, nivel general), desde ene-2017."""
    try:
        hoja = pd.read_excel(io.BytesIO(_get(URL_INDEC_IPC).content),
                             sheet_name="Índices IPC Cobertura Nacional", header=None, nrows=15)
        f_fechas = _buscar_fila(hoja, "Total nacional")
        f_nivel = next(i for i in range(f_fechas + 1, len(hoja))
                       if str(hoja.iat[i, 0]).strip().lower() == "nivel general")
        fechas = hoja.iloc[f_fechas, 1:].map(_fecha_es)
        nivel = pd.to_numeric(hoja.iloc[f_nivel, 1:], errors="coerce")
        s = pd.Series(nivel.values, index=pd.DatetimeIndex(fechas.values)).dropna()
        s = s[s.index.notna()].sort_index()
        infl = s.pct_change().dropna()
        fuente = "IPC Nacional (INDEC, base dic-2016)"
    except Exception as e:  # noqa: BLE001
        print(f"  INDEC falló ({e}); uso datos.gob.ar")
        d = pd.read_csv(io.StringIO(_get(URL_DATOSGOB_IPC).text))
        infl = pd.Series(d.iloc[:, 1].values, index=pd.to_datetime(d.iloc[:, 0])).dropna()
        fuente = "IPC Nacional (INDEC vía datos.gob.ar)"
    infl = infl[infl.index >= DESDE_IPC_NACIONAL]
    return pd.DataFrame({"mes": infl.index, "inflacion": infl.values, "fuente": fuente})


# ---------------------------------------------------------------- CPI Estados Unidos
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SERIE_CPI = "CPIAUCSL"   # = BLS CUSR0000SA0, desestacionalizado (como el Excel). Alternativa: CPIAUCNS


def _fred(serie: str) -> pd.Series:
    d = pd.read_csv(io.StringIO(_get(FRED_CSV.format(serie)).text))
    d.columns = ["fecha", "valor"]
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce")   # FRED usa "." para faltantes
    return pd.Series(d["valor"].values, index=_mes(d["fecha"])).dropna()


def cpi_usa() -> pd.DataFrame:
    s = _fred(SERIE_CPI)
    return pd.DataFrame({"mes": s.index, "cpi": s.values})


# ---------------------------------------------------------------- ITCRM (BCRA)
URL_ITCRM = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/ITCRMSerie.xlsx"


def itcrm() -> pd.DataFrame:
    """ITCRM y bilateral con EE.UU., promedio mensual, normalizados al último mes = 1."""
    hojas = pd.read_excel(io.BytesIO(_get(URL_ITCRM).content), sheet_name=None, header=None)
    hoja = next((h for n, h in hojas.items() if "prom" in n.lower() and "mens" in n.lower()), None)
    if hoja is None:
        raise ValueError(f"ITCRMSerie.xlsx: no está la hoja de promedios mensuales (hojas: {list(hojas)})")
    h = _buscar_fila(hoja, "Período")
    enc = [str(v).strip() for v in hoja.iloc[h]]
    c_per = enc.index("Período")
    c_m = enc.index("ITCRM")
    c_usa = next(i for i, v in enumerate(enc) if v.startswith("ITCRB Estados Unidos"))
    d = hoja.iloc[h + 1:, [c_per, c_m, c_usa]].copy()
    d.columns = ["mes", "itcrm", "usa"]
    d["mes"] = pd.to_datetime(d["mes"], errors="coerce")
    d = d.dropna(subset=["mes"])
    d["mes"] = _mes(d["mes"])
    for c in ("itcrm", "usa"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna().sort_values("mes")
    u = d.iloc[-1]
    return pd.DataFrame({"mes": d["mes"], "itcrm_norm": d["itcrm"] / u["itcrm"],
                         "itcrb_usa_norm": d["usa"] / u["usa"]})


# ---------------------------------------------------------------- TWDI (FRED)
INICIO_RTWEXBGS = pd.Timestamp("2006-01-01")


def twdi(historico: pd.DataFrame) -> pd.DataFrame:
    """Índice real amplio del dólar. Hasta dic-2005 se conserva el empalme TWEXBPA ya guardado
    (serie discontinuada); desde ene-2006 se usa RTWEXBGS (bienes y servicios)."""
    nuevo = _fred("RTWEXBGS")
    hist = historico.set_index(pd.to_datetime(historico["mes"]))["twdi"]
    hist = hist[hist.index < INICIO_RTWEXBGS]
    s = pd.concat([hist, nuevo[nuevo.index >= INICIO_RTWEXBGS]])
    return pd.DataFrame({"mes": s.index, "twdi": s.values})


# ---------------------------------------------------------------- Bandas cambiarias (BCRA)
URL_BANDAS = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/serie-completa-bandas-cambiarias.xlsx"
DESDE_BANDAS_2026 = pd.Timestamp("2026-01-01")


def bandas() -> pd.DataFrame:
    """Promedio mensual de las bandas vigentes desde ene-2026. Toma las columnas cuyo
    encabezado contiene 'Inferior' / 'Superior' (las últimas, si hay varios regímenes)."""
    hojas = pd.read_excel(io.BytesIO(_get(URL_BANDAS).content), sheet_name=None, header=None)
    for nombre, hoja in hojas.items():
        try:
            h = _buscar_fila(hoja, "Fecha")
        except ValueError:
            continue
        enc = [str(v).strip() for v in hoja.iloc[h]]
        inf = [i for i, v in enumerate(enc) if "inferior" in v.lower()]
        sup = [i for i, v in enumerate(enc) if "superior" in v.lower()]
        if not (inf and sup):
            continue
        d = hoja.iloc[h + 1:, [enc.index("Fecha"), inf[-1], sup[-1]]].copy()
        d.columns = ["fecha", "inf", "sup"]
        d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce", dayfirst=True)
        d[["inf", "sup"]] = d[["inf", "sup"]].apply(pd.to_numeric, errors="coerce")
        d = d.dropna()
        d = d[d["fecha"] >= DESDE_BANDAS_2026]
        g = d.groupby(_mes(d["fecha"]))[["inf", "sup"]].mean()
        return pd.DataFrame({"mes": g.index, "banda_inferior": g["inf"].values,
                             "banda_superior": g["sup"].values})
    raise ValueError(f"bandas: no encontré columnas Fecha/Inferior/Superior (hojas: {list(hojas)})")
