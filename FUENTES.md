# Fuentes de datos

Cada serie usada en el cálculo vive en un CSV de `data/raw/`. Esta tabla documenta de dónde sale cada uno, cómo se actualiza y qué transformación se le aplica. Los tramos marcados como **congelados** no se vuelven a descargar: son datos históricos que se migraron del Excel original ("Dólar Real Mensual.xlsx", oct-2026) con `scripts/semilla_desde_excel.py`.

| Archivo | Contenido | Fuente | Actualización |
|---|---|---|---|
| `tc_oficial_diario_1970_2019.csv` | Tipos de cambio diarios (único, financiero, libre, oficial, Com. A 3500) y factor de conversión de signos monetarios | Ministerio de Hacienda, SSPM, [Tipos de cambio históricos](https://datos.gob.ar/dataset/sspm-tipos-cambio-historicos) (descargado 24-ene-2020), con correcciones manuales | Congelado |
| `tc_oficial_mensual.csv` | TC oficial, promedio mensual, en pesos actuales | Hasta oct-2019: derivado del archivo anterior. Desde nov-2019: BCRA, [Com. A 3500](https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/com3500.xls), hoja "TCR diario y TCNPM" | Mensual desde nov-2019 |
| `blue_diario_ambito_hasta_2022.csv` | Dólar informal diario, compra y venta | [Ámbito, histórico dólar informal](https://www.ambito.com/contenidos/dolar-informal-historico.html) | Congelado |
| `blue_diario_desde_2023.csv` | Dólar informal diario desde 2023 | Ámbito (`mercados.ambito.com/dolar/informal/historico-general/...`). Respaldo: [ArgentinaDatos](https://api.argentinadatos.com/v1/cotizaciones/dolares/blue) | Mensual (lo crea la primera corrida) |
| `blue_mensual.csv` | Blue, promedio mensual de la venta. Sólo 2011–2015 y desde ago-2019 | Derivado de los dos anteriores | Mensual desde ene-2023 |
| `inflacion_argentina_mensual.csv` | Variación mensual del IPC empalmado; columna `fuente` indica el índice de cada tramo | Ver detalle abajo | Mensual desde ene-2017 |
| `cpi_usa_mensual.csv` | CPI-U, all items, desestacionalizado (BLS `CUSR0000SA0`) | [FRED CPIAUCSL](https://fred.stlouisfed.org/series/CPIAUCSL) (misma serie que BLS) | Mensual, serie completa |
| `itcrm_bcra_normalizado.csv` | ITCRM y bilateral con EE.UU., promedio mensual, normalizados al último mes = 1 | BCRA, [ITCRMSerie.xlsx](https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/ITCRMSerie.xlsx), hoja "ITCRM y bilaterales prom. mens." | Mensual, serie completa |
| `twdi_fred_mensual.csv` | Índice real amplio del dólar (Reserva Federal) | Hasta dic-2005: [TWEXBPA](https://fred.stlouisfed.org/series/TWEXBPA) (bienes, discontinuada) reescalada al nivel de RTWEXBGS en ene-2006. Desde ene-2006: [RTWEXBGS](https://fred.stlouisfed.org/series/RTWEXBGS) | Congelado hasta 2005, mensual desde 2006 |
| `bandas_cambiarias_mensual.csv` | Bandas cambiarias, promedio mensual | BCRA: 2025 [serie-completa-bandas-cambiarias-2025.xlsx](https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/serie-completa-bandas-cambiarias-2025.xlsx) (congelado); desde 2026 [serie-completa-bandas-cambiarias.xlsx](https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/serie-completa-bandas-cambiarias.xlsx) | Mensual desde ene-2026 |

`config/eventos.csv` lista los eventos que se marcan en el gráfico (mes, nombre, serie). Se edita a mano.

## Inflación de Argentina

Se usa la misma serie que el BCRA para el tipo de cambio real multilateral ([metodología ITCRM](http://www.bcra.gov.ar/Pdfs/PublicacionesEstadisticas/TCRMMetodologia.pdf)), empalmada hacia atrás:

| Desde | Hasta | Índice | Origen |
|---|---|---|---|
| 1943 | dic-2006 | IPC GBA (INDEC) | datos.gob.ar `178.1_NL_GENERAL_0_0_13` |
| ene-2007 | jul-2012 | IPC San Luis | datos.gob.ar `197.1_NIVEL_GENERAL_2014_0_13` |
| ago-2012 | abr-2016 | Promedio simple de variaciones IPC CABA e IPC San Luis | datos.gob.ar `193.1_NIVEL_GENERAL_JULI_0_13` y `197.1_...` |
| may-2016 | dic-2016 | IPC GBA (INDEC, base abr-2016) | datos.gob.ar `104.1_I2NG_2016_M_20` |
| ene-2017 | hoy | IPC Nacional (INDEC, base dic-2016) | [INDEC sh_ipc_divisiones.xls](https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_divisiones.xls), hoja "Índices IPC Cobertura Nacional". Respaldo: datos.gob.ar `145.3_INGNACNAL_DICI_M_15` |

Sólo el último tramo se descarga cada mes; los anteriores están congelados.

## Tipo de cambio 1970–2019: criterios y correcciones

Tomado del Excel original (hoja "Parámetros"):

- Para cada día se toma el máximo entre los distintos tipos de cambio publicados, se convierte a pesos actuales con el factor de conversión de signos monetarios y se promedia por mes.
- 3/1/1983 a 1/6/1983: símbolo decimal mal puesto en la fuente; se dividió por 10.
- 1/11/1982 a 31/12/1982 y 20/5/1989 a 11/12/1989: se usaron como valores diarios los promedios de [Series históricas de estadísticas monetarias](https://datos.gob.ar/dataset/sspm-series-historicas-estadisticas-monetarias), más razonables que los de la serie.
- 27/4/1989 a 19/5/1989: valores tomados a mano del BCRA (Evolución de la moneda, consultado 1/2/2019).
- 4/1/1990 a 2/1/1992: se multiplicó por 100 (punto decimal mal puesto en la fuente).

## CPI de EE.UU.: nota

Se usa la serie desestacionalizada, como en el Excel original. El IPC argentino no está desestacionalizado; para mayor consistencia podría usarse `CPIAUCNS` (cambiar `SERIE_CPI` en `src/dolar_real/fuentes.py`). En niveles de largo plazo la diferencia es despreciable. El dato de oct-2025 no fue publicado (cierre del gobierno de EE.UU.) y se interpola.
