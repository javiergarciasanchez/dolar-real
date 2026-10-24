// Consulta "USA CPI" del libro: CPI-U sin desestacionalizar (FRED CPIAUCNS = BLS CUUR0000SA0).
// Lee el CSV que el pipeline guarda en el repositorio. Columnas: Fecha, CPI.
// Los meses sin dato (oct-2025, no publicado) quedan con CPI vacío; la tabla los completa
// con su columna "CPI corregido".
let
    Url = "https://raw.githubusercontent.com/javiergarciasanchez/dolar-real/main/data/raw/cpi_usa_mensual.csv",
    Origen = Csv.Document(Web.Contents(Url), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {{"mes", type date}, {"cpi", type number}}, "en-US"),
    Meses = List.Generate(() => List.Min(Tipos[mes]), each _ <= List.Max(Tipos[mes]), each Date.AddMonths(_, 1)),
    Todos = Table.FromList(Meses, Splitter.SplitByNothing(), {"Fecha"}),
    Unido = Table.NestedJoin(Todos, {"Fecha"}, Tipos, {"mes"}, "Datos", JoinKind.LeftOuter),
    Expandido = Table.ExpandTableColumn(Unido, "Datos", {"cpi"}, {"CPI"}),
    Orden = Table.Sort(Expandido, {{"Fecha", Order.Descending}}),
    TiposFinales = Table.TransformColumnTypes(Orden, {{"Fecha", type date}, {"CPI", type number}})
in
    TiposFinales
