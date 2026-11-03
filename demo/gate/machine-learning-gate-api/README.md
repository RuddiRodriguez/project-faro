# Gate — reads demo user permissions

Send a user ID. Gate reads `users.json`, checks that the account is active, and returns its saved company and permitted terminals. Unknown or disabled users receive a 403 response. An active user with no permitted terminals receives an empty list.

This is demo user selection, not real sign-in. There are no passwords, sessions, expiry checks or AI calls. Selecting Maria's ID does not prove you are Maria. Run locally only.

## Example

Request to `POST /v1/access`:

```json
{"user_id": "ana"}
```

Response:

```json
{
  "user_id": "ana",
  "company_id": "harbor",
  "permitted_scope_ids": ["harbor_north"],
  "permission_version": "v1"
}
```

Company and terminals come from the saved record, never from extra values in the request. Files are read again on each call, so permission changes apply to the next request.

Compass will later pass the company and terminal fields to Library. Compass is not implemented yet. A local test verifies that Gate's output can supply Library's input.

## Implementation

The API calls AccessChecker.check. API and library inputs and outputs are separate Pydantic classes. Gate reads the selected demo account and its permitted company information.

## Run

From the demo folder:

```sh
cd /Users/ruddigarcia/Projects/assesment/demo
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn gate_api.infer:app --host 127.0.0.1 --port 8002
```

```sh
curl http://127.0.0.1:8002/v1/access \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"ana"}'
```

Set `FARO_DATA_PATH` to use another folder containing `users.json`. Default: existing demo dataset.

## Tests

From the demo folder:

```sh
venv/bin/python -m unittest discover -s gate/machine-learning-gate-api/tests -v
```
