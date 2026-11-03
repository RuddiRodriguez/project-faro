# Library — reads saved company information

Library is the first working service in the Faro demo. It reads the existing JSON collections. It does not call AI or read crane activity rows.

## Example

Input to `POST /v1/company-information`:

```json
{
  "company_id": "harbor",
  "permitted_scope_ids": ["harbor_north"]
}
```

Library reads companies, terminals, documents and agreements. It returns Harbor's company information, North Terminal, four approved definition documents and North's approved agreement. South's terminal and agreement are excluded, as is all material from other companies.

The API and library each have Pydantic input and output classes. The endpoint converts the fields explicitly and calls InformationReader.read.

## Selection rules

- Company and terminal IDs must match saved information. Unknown companies or terminals outside that company produce an error.
- With no permitted terminals, the response contains company information and empty terminal, document and agreement lists.
- Only approved documents and agreements are returned.
- The existing definition documents apply to each terminal listed on them. Library returns a document when at least one of those terminals is permitted, and returns only permitted terminal IDs. This filters documents, not sentences: a document containing restricted details must be stored separately with the correct permissions.
- Agreement dates and document versions remain in the response. Library does not choose which agreement applies to a question's period; that belongs to later processing.
- Files are read on every call, so changes are visible on the next call. Caching is not implemented yet.

## Who supplies permissions?

Eventually Compass will supply the company and terminals verified by Gate. This local API currently accepts those values directly for testing. It does not authenticate a user or prove they are allowed to request those terminals. Gate and Compass are not implemented yet; this API is not ready for public access.

## Run locally

From the demo folder, using the shared environment:

```sh
cd /Users/ruddigarcia/Projects/assesment/demo
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn library_api.infer:app --host 127.0.0.1 --port 8001
```

The interactive API page is `http://127.0.0.1:8001/docs`.

`FARO_DATA_PATH` can point to another folder containing the same four JSON collections. The default is the existing demo dataset.

```sh
curl http://127.0.0.1:8001/v1/company-information \
  -H 'Content-Type: application/json' \
  -d '{"company_id":"harbor","permitted_scope_ids":["harbor_north"]}'
```

## Tests

Run from the demo folder:

```sh
venv/bin/python -m unittest discover -s library/machine-learning-library-api/infer/library/tests -v
venv/bin/python -m unittest discover -s library/machine-learning-library-api/tests -v
```

The API and library are separate installable packages. Their existing folders remain ready to become separate repositories; no remote repositories or submodules have been created.
