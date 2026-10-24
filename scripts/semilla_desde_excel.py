"""Genera los CSV semilla de data/raw/ a partir del libro histórico "Dólar Real Mensual.xlsx".

Se corrió una sola vez (oct-2026) para migrar el Excel al repositorio. Queda como registro
de cómo se obtuvieron las series históricas que ya no se descargan (ver FUENTES.md).

Uso:  python scripts/semilla_desde_excel.py "ruta/Dólar Real Mensual.xlsx"
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIX = ROOT / "tests" / "fixtures"


def mes(s):
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()


def guardar(df, nombre, carpeta=RAW):
    carpeta.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(df.columns[0]).reset_index(drop=True)
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    df.to_csv(carpeta / nombre, index=False, float_format="%.10g")
    print(f"{nombre}: {len(df)} filas")


def main(xlsx):
    rd = lambda sheet, cols, header=0: pd.read_excel(xlsx, sheet_name=sheet, usecols=cols, header=header)

    # 1. Tipo de cambio oficial diario 1970-01 a 2019-10 (datos.gob.ar, con correcciones manuales)
    d = rd("Dolar 1970-01 - 2019-10", "A:M", header=5).rename(columns={"indice_tiempo": "fecha", "Factor Conv": "factor_conversion"})
    guardar(d, "tc_oficial_diario_1970_2019.csv")

    # 2. Tipo de cambio oficial mensual (serie empalmada; desde 2019-11 se actualiza con BCRA Com. A 3500)
    m = rd("Dolar Mensual", "A:B").rename(columns={"Mes": "mes", "Dolar_Prom_Mensual": "tc_oficial"})
    m["mes"] = mes(m["mes"])
    guardar(m, "tc_oficial_mensual.csv")

    # 3. Dólar blue diario 2011-2022 (Ámbito, histórico congelado)
    b = rd("Dolar Blue - Fuent Ambito", "A:C").rename(columns={"Fecha": "fecha", "Compra": "compra", "Venta": "venta"})
    guardar(b.dropna(subset=["fecha"]), "blue_diario_ambito_hasta_2022.csv")

    # 4. Dólar blue mensual (promedio de la cotización de venta)
    bm = rd("Dolar Blue", "A:B").rename(columns={"Mes": "mes", "Blue": "blue"})
    bm["mes"] = mes(bm["mes"])
    guardar(bm, "blue_mensual.csv")

    # 5. Inflación Argentina mensual empalmada (metodología BCRA-ITCRM)
    i = rd("Inflac Arg", "A:B").rename(columns={"Mes": "mes", "Inflación": "inflacion"})
    i["mes"] = mes(i["mes"])
    tramos = [("1900-01-01", "2006-12-01", "IPC GBA (INDEC, base 1999)"),
              ("2007-01-01", "2012-07-01", "IPC San Luis"),
              ("2012-08-01", "2016-04-01", "Promedio variaciones IPC CABA e IPC San Luis"),
              ("2016-05-01", "2016-12-01", "IPC GBA (INDEC, base abr-2016)"),
              ("2017-01-01", "2100-01-01", "IPC Nacional (INDEC, base dic-2016)")]
    i["fuente"] = ""
    for desde, hasta, f in tramos:
        i.loc[i["mes"].between(desde, hasta), "fuente"] = f
    guardar(i, "inflacion_argentina_mensual.csv")

    # 6. CPI USA (BLS, CUSR0000SA0, desestacionalizado)
    c = rd("USA CPI", "A:B").rename(columns={"Fecha": "mes", "CPI": "cpi"})
    c["mes"] = mes(c["mes"])
    guardar(c.dropna(), "cpi_usa_mensual.csv")

    # 7. ITCRM y bilateral USA (BCRA), normalizados al último mes = 1
    t = rd("TCRM", "A:C").rename(columns={"Fecha": "mes", "TCRM": "itcrm_norm", "TCRB_USA": "itcrb_usa_norm"})
    t["mes"] = mes(t["mes"])
    guardar(t.dropna(), "itcrm_bcra_normalizado.csv")

    # 8. Índice real del dólar (FRED, empalme TWEXBPA -> RTWEXBGS)
    w = rd("TWDI", "A:B").rename(columns={"Mes": "mes", "TWDI": "twdi"})
    w["mes"] = mes(w["mes"])
    guardar(w.dropna(), "twdi_fred_mensual.csv")

    # 9. Bandas cambiarias (BCRA), promedio mensual
    bc = rd("Bandas Cambiarias", "A:C").rename(columns={"Mes": "mes", "Banda Inferior": "banda_inferior", "Banda Superior": "banda_superior"})
    bc["mes"] = mes(bc["mes"])
    guardar(bc.dropna(subset=["mes"]), "bandas_cambiarias_mensual.csv")

    # Referencia para tests: resultado del Excel (hoja "Dólar Real Form")
    f = pd.read_excel(xlsx, sheet_name="Dólar Real Form", header=18, usecols="A:W")
    f = f[pd.to_datetime(f["Mes"], errors="coerce").notna()].copy()
    f["Mes"] = mes(f["Mes"])
    guardar(f, "excel_dolar_real_form.csv", FIX)


if __name__ == "__main__":
    main(sys.argv[1])
