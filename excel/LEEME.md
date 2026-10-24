# Excel de clase

El Excel de clase deja de descargar las fuentes una por una. Lee una sola serie ya calculada, `dolar_real.csv`, publicada en GitHub Pages. El cálculo sigue a la vista en el libro para los alumnos: la columna del factor de inflaciones, los valores reales y los promedios vienen en el CSV, y las fórmulas pueden reconstruirse sobre las columnas nominales e inflaciones.

## Conectar el libro

1. En Excel: **Datos > Obtener datos > Desde otras fuentes > Consulta en blanco**.
2. **Editor avanzado**, pegar el contenido de `consulta_powerquery.m` (ya apunta a `https://javiergarciasanchez.github.io/dolar-real/dolar_real.csv`).
3. Nombrar la consulta `Dolar_Real` y **Cerrar y cargar en** una tabla de una hoja nueva ("Datos").
4. Apuntar los gráficos a las columnas de esa tabla. Como la tabla crece sola, los gráficos se actualizan sin insertar filas.
5. Cada mes: **Datos > Actualizar todo**.

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
