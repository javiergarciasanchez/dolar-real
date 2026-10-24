# Dólar Real Argentina — contexto para Claude Code

Proyecto de Javier (profesor de Finanzas, director del EMBA del IAE). Migra el libro "Dólar Real Mensual.xlsx" (OneDrive, carpeta Finanzas Internacionales) a código: un pipeline en Python que descarga las fuentes, calcula el tipo de cambio real y publica una página en GitHub Pages más un CSV que lee el Excel de clase. Respuestas en español, concisas y en prosa.

## Reglas

- El código vive en `C:\Projects\Dólar Real` (este repo). En la carpeta de OneDrive "Finanzas Internacionales" sólo van archivos de salida, nunca código.
- Los insumos se guardan como CSV en `data/raw/` y cada uno está documentado en `FUENTES.md`. Si se agrega o cambia una fuente, actualizar `FUENTES.md` en el mismo cambio.
- `tests/test_calculo.py` debe seguir pasando: verifica que el cálculo reproduce el Excel original (mes base sep-2026). No cambiar la metodología sin acordarlo con Javier.
- No poner claves de API en el código. FRED se lee por `fredgraph.csv`, que no requiere clave.

## Estado (oct-2026, armado en Cowork)

Hecho y verificado:
- CSV semilla extraídos del Excel (`scripts/semilla_desde_excel.py`).
- `calculo.py` reproduce las columnas del Excel con error relativo < 1e-6 (11 tests).
- `publicar.py` genera `docs/data.json` y `docs/dolar_real.csv`; `docs/index.html` probado con esos datos.
- Workflow de GitHub Actions y consulta Power Query escritos.

Probado contra las fuentes reales en la PC de Javier (24-oct-2026, Claude Code):
- Las 7 fuentes de `fuentes.py` descargan y reproducen los CSV semilla (error relativo ≤ 1e-9, salvo inflación: ≤ 0,0066 p.p. en may/jun-2022 y revisiones menores en 2025-26).
- Corregido: Ámbito devuelve fechas `dd/mm/aaaa` (el parser esperaba guiones). Los días repetidos de Ámbito se conservan porque así promediaba el Excel; sin ellos el blue mensual cambia hasta 4%.
- Corregido: en el .xls del INDEC la columna de mar-2026 es la fecha 26/03/2026; `_fecha_es` ahora lleva todo al día 1.
- El respaldo ArgentinaDatos funciona pero difiere hasta 5,5% de Ámbito en promedios mensuales.
- Avisos esperables en `estado.json`: saltos en ene-2002 y dic-2023 (devaluaciones), CPI oct-2025 faltante.
- `ci/actualizar.yml` ya está en `.github/workflows/`.
- `test_calculo.py` usa una copia congelada de los insumos del Excel (`tests/fixtures/insumos_excel/`); antes leía `data/raw/` y se rompía con cada revisión de una fuente.
- Repo público `javiergarciasanchez/dolar-real`, Pages en https://javiergarciasanchez.github.io/dolar-real/ (la página dice sólo IAE Business School).
- CPI de EE.UU.: decidido usar `CPIAUCNS` (sin desestacionalizar, como el IPC argentino). También se cambió la consulta "USA CPI" del libro "Dólar Real Mensual.xlsx" a `CUUR0000SA0`.
- Excel por automatización (COM): se cae si se edita mientras el libro termina de cargar, al cambiar `Queries(...).Formula` o al tocar el hipervínculo de la hoja "USA CPI". Lo que funcionó: editar la consulta y las celdas en el XML del paquete y usar Excel sólo para refrescar y guardar.

## Próximos pasos, en orden

1. Instalar GitHub CLI (`winget install GitHub.cli`, luego `gh auth login`). Crear el repo (`gh repo create`), subir, activar Pages desde `main` / carpeta `docs`, y lanzar el workflow a mano (`gh workflow run actualizar.yml`).
2. Si BCRA o INDEC bloquean los servidores de GitHub (corren en EE.UU.), plan B: correr `actualizar` en la PC con el Programador de tareas de Windows y hacer `git push` desde ahí; el workflow queda sólo para recalcular.
3. Conectar el Excel de clase (`excel/LEEME.md`) y guardar una copia actualizada en OneDrive.

## Decisiones pendientes de Javier

- Rotar la clave de FRED que quedó guardada dentro de las consultas del Excel compartido.

## Comandos

```
pytest                                       # tests
python -m dolar_real.actualizar              # descarga + cálculo + docs/
python -m dolar_real.actualizar --offline    # sólo cálculo + docs/
python -m http.server -d docs 8000           # ver la página en http://localhost:8000
```
