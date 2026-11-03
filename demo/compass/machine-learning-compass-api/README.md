# Compass — coordinates Gate, Library, Thread, Scout, Signal, Guide, Bridge and Shield

Compass receives the user ID, latest message and previous conversation. It calls the existing services through their APIs in order:

1. Gate reads the user's saved permissions.
2. Library returns company information within those permissions.
3. A first question passes unchanged. Thread combines a clarification reply with the original question.
4. Scout searches the permitted documents for the rewritten question.
5. Compass checks each match against Library, then calls Signal with the permitted evidence.
6. Signal returns Continue, Ask or Unsupported. Compass includes that decision in its response.

Compass does not call AI itself, read the JSON dataset or recreate any existing service logic. It uses the same endpoint/library structure and explicit field mappings across Faro services.

## Example

Request to `POST /v1/questions`:

```json
{
  "user_id": "ana",
  "question": "North Terminal.",
  "conversation": [
    {"role": "user", "content": "Which cranes performed badly last month?"},
    {"role": "assistant", "content": "Which terminal?"}
  ]
}
```

Gate supplies Harbor and Ana's permitted North Terminal. Library returns the corresponding company documents and agreements. Thread receives only the latest message and conversation; it does not choose or change permissions.

Response fields:

- `question`: the original message, here `North Terminal.`
- `rewrite.question`: the full question returned by Thread, such as `Which cranes performed badly last month at North Terminal?`
- `rewrite.used_ai`, `rewrite.model_name`, `rewrite.token_usage`: Thread's existing response fields.
- `search`: the question Scout searched and the matching definitions.
- `access`: Gate's response.
- `company_information`: Library's response.

With no conversation, Thread returns the original question unchanged without an AI call. Compass still calls Thread's API; it does not duplicate that decision.

The caller supplies messages for the current user's conversation. A returned conversation ID continues stored turns after checking ownership and current access. Gate remains demo user selection rather than real sign-in. Rewriting a question does not establish that the company can answer it; Scout finds matching definitions; Signal decides whether the question is clear enough.

## Errors

Unknown or disabled users receive 403 and stop before later services. An unavailable service returns 503. An unsuccessful or invalid service response returns 502. Compass does not present a partial response as success. Gate/Library calls retain their existing 10-second timeout. Thread's call allows 40 seconds for its existing 30-second prediction timeout. The application cache and conversation records are described below.

## Run the services

From `/Users/ruddigarcia/Projects/assesment/demo`, install dependencies once:

```sh
venv/bin/python -m pip install -r requirements.txt
```

Run each command in a separate terminal from that folder:

```sh
venv/bin/python -m uvicorn gate_api.infer:app --host 127.0.0.1 --port 8002
```

```sh
venv/bin/python -m uvicorn library_api.infer:app --host 127.0.0.1 --port 8001
```

```sh
venv/bin/python -m uvicorn thread_api.infer:app --host 127.0.0.1 --port 8003
```

```sh
venv/bin/python -m uvicorn scout_api.infer:app --port 8004
```

```sh
venv/bin/python -m uvicorn compass_api.infer:app --host 127.0.0.1 --port 8000
```

Test through Compass:

```sh
curl http://127.0.0.1:8000/v1/questions \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"ana","question":"North Terminal.","conversation":[{"role":"user","content":"Which cranes performed badly last month?"},{"role":"assistant","content":"Which terminal?"}]}'
```

`FARO_GATE_URL`, `FARO_LIBRARY_URL`, `FARO_THREAD_URL` and `FARO_SCOUT_URL` override the service addresses. Thread loads the existing OpenAI key from the demo `.env`.

Run Signal on port 8005 with `venv/bin/python -m uvicorn signal_api.infer:app --port 8005`. The response includes `decision.action` and `decision.missing_choice`. Use `FARO_SIGNAL_URL` to override its address.

Before starting Compass, prepare the [Scout model](../../scout/machine-learning-scout-api/README.md) and run Scout on port 8004. The response includes `search.query` and the permitted matching definitions in `search.matches`.

## Test

Local HTTP tests, without paid AI calls:

```sh
venv/bin/python -m unittest discover -s compass/machine-learning-compass-api/tests -v
```

Full HTTP flow including real OpenAI rewrite and Decisions calls:

```sh
FARO_RUN_LIVE_TESTS=1 venv/bin/python -m unittest discover -s compass/machine-learning-compass-api/tests -v
```

Tests start temporary local servers and stop them afterward. Cases cover company/terminal separation, missing inputs, denied users, unavailable Library/Thread, a first message without AI, a clarification reply and a hotel question. Harbor cannot borrow hotel data. Separate live cases verify rankings for a hotel headquarters user, a local manager and a hospital network.

Guide runs on port 8006. [Guide instructions](../../guide/machine-learning-guide-api/README.md). Only Ask calls Guide. Compass returns the generated question in `followup.followup_text`; pass that text in the next request’s conversation with the original question when Maria replies.

On Continue, Compass sends the question and Library’s full list of permitted document IDs to Bridge and Shield. Scout’s matches do not limit access to other permitted material. Bridge can make successive reads; Shield replays them and checks each finding before Compass releases it. If a user choice is missing, Guide asks for it instead.

After Shield, Compass calls [Voice](../../voice/machine-learning-voice-api/README.md) on port 8009. Read `answer.text` for the explanation; `answer.sources` identifies the sources.

[What Compass saves, how to continue a conversation, and how cache reuse works](DATA_COLLECTION.md).
