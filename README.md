# Dólar Real Argentina

Tipo de cambio real de Argentina desde 1970, en pesos del último mes con datos. Reemplaza el libro "Dólar Real Mensual.xlsx".

- **Página web:** `docs/index.html`, publicada con GitHub Pages.
- **Serie para Excel:** `docs/dolar_real.csv` (la lee el Excel de clase; ver `excel/LEEME.md`).
- **Actualización:** GitHub Actions corre el día 16 y 20 de cada mes (`.github/workflows/actualizar.yml`), después de que INDEC publica el IPC.
- **Fuentes:** documentadas en [FUENTES.md](FUENTES.md).

## Cálculo

TCR(t) = TC(t) × Π_{k=t+1..base} (1 + π_ARG,k) / (1 + π_USA,k)

El mes base es el último con inflación publicada en ambos países. El código está en `src/dolar_real/calculo.py` y `tests/test_calculo.py` verifica que reproduce el Excel original.

## Uso local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install -e .
pytest
python -m dolar_real.actualizar            # descarga, valida, recalcula y regenera docs/
python -m dolar_real.actualizar --offline  # sólo recalcula
```

`data/estado.json` registra qué fuentes se actualizaron y hasta qué mes. Si una fuente falla, se conserva su dato anterior y el proceso termina con error (GitHub avisa por mail).

## Estructura

```
config/eventos.csv          eventos marcados en el gráfico (editar a mano)
data/raw/                   insumos, un CSV por fuente
data/estado.json            resultado de la última actualización
docs/                       sitio publicado (index.html, data.json, dolar_real.csv)
excel/                      consulta Power Query para el Excel de clase
scripts/                    migración inicial desde el Excel
src/dolar_real/             fuentes.py (descargas), calculo.py, publicar.py, actualizar.py
tests/                      tests del cálculo y de los parsers
```
