# Bridge — answers a question using the client's permitted records

Gate identifies the company and locations. Library supplies the full set of permitted documents; Scout's search results do not limit what Bridge can inspect. The source reader builds a catalogue of permitted inventory, activity fields, approved meanings, agreements and reported coverage. The catalogue describes available data; it does not establish a performance result.

Bridge calls the model through shared utils. The model can request a pandas read, inspect the returned evidence, request another read, or answer. The prompt specifies evidence and access requirements, not an analysis method. A response consists of findings with references: 0 means catalogue, and positive IDs identify successful reads. Bridge allows six model steps per request and stops without a speculative answer if they run out.

Each read runs on the selected company's checked JSON records in memory. On macOS the worker drops host permissions before evaluating the expression: network, file writes, other client files and subprocesses are unavailable. The worker has CPU, elapsed-time and result-size limits. It returns scalars, Series or tables; there is no list of permitted pandas analysis methods. On other platforms the runner fails closed until an equivalent sandbox is configured.

Shield replays every read, compares its records, version and outputs, checks the catalogue fingerprint and reviews the findings against their cited evidence. Voice displays the reviewed wording. A reviewer's model judgment is not a guarantee that the client's source records are correct.

Run from demo: `venv/bin/python -m uvicorn bridge_api.infer:app --port 8007`. Endpoint: `POST /v1/evidence`.
