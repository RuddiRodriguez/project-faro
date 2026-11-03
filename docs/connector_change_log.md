# Faro connector | 3 November 2026

The client grants access and asks a question. In this example one Harbor release consists of three actual files, created as demo fixtures. There is no client-supplied mapping form and no Python list of business terms.

| Requirement | Status and evidence |
|---|---|
| Separate service, same API and library style | Complete for the demo. [Connector library, interface and limits](../demo/connector/machine-learning-connector-api/README.md); [shared Pydantic contracts](../demo/api_objects/faro/connector). The console starts eleven APIs. |
| Read SQLite, Excel and a text PDF together | Complete for the included files. [Release generator](../demo/scripts/create_connector_sources.py) and [fixtures](../demo/connector/fixtures). SQLite contains current postings, corrections and a withdrawal; Excel contains assignments; page 1 of the PDF explains the relationship. |
| Keep the connector general | Implemented and tested for these formats. [Reader registry](../demo/connector/machine-learning-connector-api/infer/connector/connector/readers.py) chooses how to open the file. No code assigns a meaning to a client column. A test added an unrelated bookings table and read its new fields without changing the service. |
| Find, read and verify | Implemented. Scout discovers sources alongside its existing definition search. Compass passes the catalogue onward. Bridge chooses fields and reads, including a supported link; Shield reopens the sources and checks the findings. Source evidence includes original references, rows, and versions. [Bridge’s connected reads](../demo/bridge/machine-learning-bridge-api/infer/bridge/bridge/connected.py). Faro’s existing prepared JSON path remains available. |
| Console and evidence checks | Complete for the stated cases. See results below. |
| Both PDFs | Regenerated and checked: 17 pages each. Sections 2.2–2.4 follow one question across three sources. No private file links in the delivery copy; 47 section-level file links in the reference copy. |

## What was reused

- Services use the shared HTTP caller to communicate.
- A dictionary selects the reader for each supported file type.
- Scout keeps its definition search. Bridge keeps its current model, shared utilities and isolated dataframe worker. Shield keeps its replay and verification path. No additional model call is required to open a file.
- Other integration changes: Connector endpoint and package metadata, console service list and URL, Scout and Bridge API objects, Signal inventory input via Compass, shared service calls, Shield evidence prompt and replay, demo dependencies and README. An empty or invalid structured response from Bridge now returns an incomplete result without figures; it no longer raises HTTP 500 in that case.

## What the tests showed

Maria signed in through the console and asked: “Which berths had the most crane idle hours last month?” In a fresh collection with no reused work, Faro returned S1: 115 h, N1: 100 h, N2: 86 h, S2: 71 h. The [saved verified turn](../demo/local_data/connector_confirm/verified_turn.json) contains the PDF read, the database/workbook join, the grouped result, and Shield’s verdict. The run took 30.3 seconds; this is one observation, not a performance benchmark.

In a second live console run the S-09 workbook assignment was removed, keeping the other records. The [saved refusal](../demo/local_data/connector_final_missing/withheld_turn.json) reports the missing assignment and gives no ranking; the internal status is Unsupported. The console also emitted a multiprocessing semaphore warning at shutdown.

Five [Connector HTTP tests](../demo/connector/machine-learning-connector-api/tests/test_sources.py) passed. They cover all three formats, source references and versions, rejection of out-of-scope reads, a correction changing the winner to N1 at 126 hours, missing or ambiguous assignments, and reading a previously unseen table. Related suites: Bridge 13 passed, Shield 13 passed, Scout 3 passed, Signal 2 passed, Compass 15 passed and 17 skipped. The skipped cases were not counted as evidence. An earlier live run hit an invalid model response; a new Bridge test covers that failure separately.

## Product limits

This is a local three-format implementation, not a general-purpose data lake. Remote database and lake connections, MongoDB, OCR, large reads, and arbitrary time-based relationships remain unbuilt. Grants apply to entire files; trusted local services supply verified access. The demo accepts up to 500 rows per item, uses an exact key match, and refuses missing or ambiguous links. It can refuse cases that a broader reader could answer. Production access control, speed at client scale, and usefulness to operators still need separate testing.

## Follow-up: source documents beside the answer

Added local document attachments to the answer. Connector stores the exact SQLite, Excel or PDF bytes used for a successful read and returns the saved filename, URI and hash. Bridge carries those references with its evidence; Voice returns them in a new Pydantic `documents` field; the console prints sources, document links and the used locations. Repeated reads of a file appear once. Files remain unchanged when an original is subsequently corrected. Legacy JSON reads return an export of the selected permitted records rather than exposing the multi-company original. No new model calls or PDF changes were needed.

Verification: six Connector tests, fourteen Bridge tests, thirteen Shield tests and five Voice tests passed; one opt-in Voice test was skipped. The final live console run returned the October berth ranking and printed all three document links with their locations, in 34 seconds without cached work. Saved answer and all attached file hashes were checked in `demo/local_data/documents_console_final/saved_turn.json`. An earlier live run declined the same question with an explicit October date before answering; this attachment feature does not resolve variability in Bridge's analysis. The console's existing semaphore shutdown warning remains.
