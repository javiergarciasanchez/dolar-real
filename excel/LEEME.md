# Excel de clase

El libro "Dólar Real Mensual.xlsx" (OneDrive, Finanzas Internacionales) lee la serie ya calculada, `dolar_real.csv`, publicada en GitHub Pages. El cálculo sigue a la vista en el libro para los alumnos: los insumos vienen del CSV y el factor de inflaciones, los valores reales y los promedios se calculan con fórmulas en la hoja "Dólar Real Form". La versión anterior, que descargaba cada fuente por su cuenta, quedó guardada como "Dólar Real Mensual - pre-github.xlsx".

## Cómo está conectado (oct-2026)

- Consulta `Dolar_Real` (texto en `consulta_powerquery.m`), cargada en la tabla `Dolar_Real` de la hoja **Datos**.
- En "Dólar Real Form", la columna de meses es `=SORT(Dolar_Real[mes],,-1)` y crece sola: ya no hay que insertar filas. Los insumos (TC oficial y blue nominales, bandas, inflaciones, ITCRM, bilateral EE.UU., brecha TWDI) son `XLOOKUP` sobre `Dolar_Real`; el resto de las columnas no cambió.
- Los tres gráficos apuntan a nombres definidos de la hoja (`GrafCorto_*` desde jun-2019, `GrafEventos_*` desde ene-2000, `GrafCompleto_*` desde ene-1970, `GrafEtiq_*` para las etiquetas de eventos) que se estiran con los meses. Las series ocultas por el filtro de cada gráfico conservan su rango fijo.
- Siguen en el libro las consultas propias de las hojas auxiliares ("Inflac Prom", "Infl Prom USA", "Proy Prom Anual", "TWDI", proyección de bandas). Las dos de FRED (TWDI) leen `fredgraph.csv`, sin clave.

## Uso mensual

Después del día 16 (cuando corre la actualización en GitHub): **Datos > Actualizar todo**.

## Conectar otro libro

1. En Excel: **Datos > Obtener datos > Desde otras fuentes > Consulta en blanco**.
2. **Editor avanzado**, pegar el contenido de `consulta_powerquery.m`.
3. Nombrar la consulta `Dolar_Real` y **Cerrar y cargar en** una tabla de una hoja nueva ("Datos").
4. Apuntar fórmulas y gráficos a las columnas de esa tabla.

## Columnas del CSV

| Columna | Significado |
|---|---|
| `mes` | Primer día del mes |
| `tc_oficial_nominal`, `tc_blue_nominal` | TC nominal promedio del mes (el blue repite el oficial donde no hubo cepo) |
| `banda_inferior_nominal`, `banda_superior_nominal` | Bandas cambiarias nominales |
| `inflacion_arg`, `inflacion_usa` | Inflación mensual |
| `factor_inflaciones` | Π de (1+π_ARG)/(1+π_USA) de los meses posteriores hasta el mes base |
| `oficial`, `blue`, `banda_inferior`, `banda_superior` | Valores reales, en pesos del mes base |
| `multilateral`, `bilateral_usa` | ITCRM y bilateral EE.UU. del BCRA, escalados al TC oficial del mes base |
| `prom_oficial`, `prom_blue`, `prom_multilateral` | Promedios históricos reales |
| `brecha_twdi` | Desvío del índice real del dólar (Fed) respecto de su promedio |
| `prom_oficial_aj_twdi`, `prom_blue_aj_twdi` | Promedios ajustados por la fortaleza global del dólar |
| `prom_oficial_corriente`, `prom_blue_corriente` | Promedio histórico expresado en pesos de cada mes |
