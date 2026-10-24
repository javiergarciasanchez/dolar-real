// Consulta "Bandas Cambiarias" del libro: promedio mensual de las bandas del BCRA, incluidos
// los meses próximos ya anunciados.
// Lee el CSV que el pipeline guarda en el repositorio. Columnas: Mes, Banda Inferior, Banda Superior.
let
    Url = "https://raw.githubusercontent.com/javiergarciasanchez/dolar-real/main/data/raw/bandas_cambiarias_mensual.csv",
    Origen = Csv.Document(Web.Contents(Url), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {{"mes", type date}, {"banda_inferior", type number}, {"banda_superior", type number}}, "en-US"),
    Columnas = Table.RenameColumns(Tipos, {{"mes", "Mes"}, {"banda_inferior", "Banda Inferior"}, {"banda_superior", "Banda Superior"}}),
    Orden = Table.Sort(Columnas, {{"Mes", Order.Descending}})
in
    Orden
