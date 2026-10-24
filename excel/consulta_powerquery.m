// Consulta Power Query para el Excel de clase.
// Dirección de GitHub Pages del repositorio javiergarciasanchez/dolar-real.
let
    Url = "https://javiergarciasanchez.github.io/dolar-real/dolar_real.csv",
    Origen = Csv.Document(Web.Contents(Url), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    SinVacios = Table.TransformColumns(Encabezados, {}, each if _ = "" then null else _),
    Columnas = Table.ColumnNames(SinVacios),
    Tipos = Table.TransformColumnTypes(
        SinVacios,
        {{"mes", type date}} & List.Transform(List.Skip(Columnas, 1), each {_, type number}),
        "en-US"
    ),
    Orden = Table.Sort(Tipos, {{"mes", Order.Descending}})
in
    Orden
