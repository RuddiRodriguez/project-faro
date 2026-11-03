# Connector — reads native sources

From `demo/`, run `venv/bin/python console.py --test`, sign in as `maria` and ask:

> Which berths had the most crane idle hours last month?

One Harbor release has three independent sources. SQLite holds the times and revisions. Excel maps posting references to berths. A text PDF defines the period, units, which events count and how to match them. The PDF does not give away the ranking. The fixture files are included; `venv/bin/python scripts/create_connector_sources.py` regenerates the fictional release. The existing JSON records are connected through the same service for other questions.

## Interface

Scout discovers available items; Bridge reads them; Shield repeats the reads. Each calls the internal Connector API. `POST /v1/sources` accepts an action (`discover`, `inspect`, `read`), the verified company and scopes, an item ID for inspect/read, and optional native field names for read. It returns native headings, file/table/sheet/page location, snapshot fingerprint and, for reads, values with row/page references. An empty discovery means no mounted file within this access scope. A service outage is an error, not an empty catalogue.

A file grant in `connector/fixtures/connections.json` contains its company, scopes and filename. A JSON grant may name the field holding row access scopes; that is an access setting, not a business interpretation. No business vocabulary or hand-written field mapping. Paths come from trusted configuration, never from the question. For another folder set `FARO_CONNECTOR_ROOT`. Each registered native reader lists items and reads fields. Register another reader in `readers.READERS`. No factory class is needed. The service has a library and API with Pydantic inputs and outputs in the shared API objects package.

## Boundaries

- SQLite, Excel and PDF use file-level access: the caller must hold every scope on the grant. JSON row access filters records using the configured access field. An internal service passes the scope supplied by Faro; this localhost demo does not authenticate arbitrary network callers.
- Read-only JSON tables, local SQLite tables/views, visible Excel sheets with a header row and text PDFs indexed by page. Workbook formulas need saved values. No OCR, general PDF table reconstruction, remote credentials, MongoDB or lake driver.
- The demo reads at most 1,000 rows per item and refuses oversized reads. It does not send a silent sample. Discovery lists accessible native items; it does not semantically rank all files or learn a glossary.
- Bridge can attach one connected table to another using model-selected native key fields. The demo requires matching key sets and an unambiguous right-side key; an unsupported relationship can be declined. This does not implement arbitrary time-range joins or infer that similar names identify the same asset.
- The source-specific meaning lives in Harbor's own release note and data. The model interprets it. Shield checks the actual source rows, reference/version and replayed results before releasing findings.

Test the connector and evidence checks from `demo/`:
`venv/bin/python -m unittest discover -s connector/machine-learning-connector-api/tests -v`.

## Open the evidence behind an answer

Whole-file reads save a byte-for-byte copy under `demo/local_data/source_documents/<company>/<version>/`.
Set `FARO_DOCUMENT_PATH` to change that location. The connector returns the copy's filename, file URI and content version. Bridge keeps this alongside the read; Voice returns `documents` with the answer and deduplicates repeated reads of the same file. The console prints those links with the source page, sheet or record references. The links point to local files, not a remotely hosted download endpoint.

For JSON grants with a row access field, Connector saves a separate `*-permitted.json` document containing only the permitted rows and requested fields. It never attaches the unfiltered file. Withheld answers have no document attachments.
