// Consulta "Inflación" del libro: inflación mensual de Argentina desde 1943 (serie empalmada, ver FUENTES.md).
// Lee el CSV que el pipeline guarda en el repositorio. Columnas: Mes, Inflación.
// La tabla agrega con fórmulas las columnas IPC y Año.
let
    Url = "https://raw.githubusercontent.com/javiergarciasanchez/dolar-real/main/data/raw/inflacion_argentina_mensual.csv",
    Origen = Csv.Document(Web.Contents(Url), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {{"mes", type date}, {"inflacion", Percentage.Type}}, "en-US"),
    Columnas = Table.RenameColumns(Table.SelectColumns(Tipos, {"mes", "inflacion"}), {{"mes", "Mes"}, {"inflacion", "Inflación"}}),
    Orden = Table.Sort(Columnas, {{"Mes", Order.Descending}})
in
    Orden
