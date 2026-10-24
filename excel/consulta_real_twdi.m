// Consulta "Real TWDI" del libro: índice real amplio del dólar (Reserva Federal), empalme
// TWEXBPA hasta 2005 y RTWEXBGS desde 2006 (ver FUENTES.md).
// Lee el CSV que el pipeline guarda en el repositorio. Columnas: Mes, TWDI, Avg TWDI, Brecha.
let
    Url = "https://raw.githubusercontent.com/javiergarciasanchez/dolar-real/main/data/raw/twdi_fred_mensual.csv",
    Origen = Csv.Document(Web.Contents(Url), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {{"mes", type date}, {"twdi", type number}}, "en-US"),
    Columnas = Table.RenameColumns(Tipos, {{"mes", "Mes"}, {"twdi", "TWDI"}}),
    Promedio = List.Average(Columnas[TWDI]),
    ConPromedio = Table.AddColumn(Columnas, "Avg TWDI", each Promedio, type number),
    ConBrecha = Table.AddColumn(ConPromedio, "Brecha", each [TWDI] / [Avg TWDI] - 1, Percentage.Type),
    Orden = Table.Sort(ConBrecha, {{"Mes", Order.Descending}})
in
    Orden
