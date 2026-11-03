# Signal — decides what happens next

Compass calls Signal after Scout. It sends the rewritten question, matching source passages, the connected source IDs and Gate's permitted scopes. Signal classifies the next action; it does not use a predefined list of supported tasks.

| Question to Compass | Signal decision |
|---|---|
| Which cranes at North Terminal had the most downtime last month? | Continue |
| Which cranes performed badly at North Terminal last month? | Ask: performance indicator |
| Show payroll for crane operators at North Terminal. | Unsupported |

Continue means the question is clear enough to check against operational data. Signal does not answer it. Ask identifies what needs clarification; Guide will ask the question in a later step. Unsupported means the available company material does not support proceeding with this request. When there are no permitted matches or no supported-tasks document, Signal stops without a model call. An unavailable service or model is an error, never an Unsupported decision.

## Run from the demo folder

Install the root requirements in the shared environment and start Signal:

```sh
venv/bin/python -m uvicorn signal_api.infer:app --port 8005
```

`POST /v1/classify` uses the existing OpenAI key in the demo environment. The API and library have separate Pydantic inputs and outputs. The library is imported as `faro_signal` to avoid shadowing Python’s built-in `signal` module.

## Implementation

The classifier delegates to quality/classifier.py. Instructions live in prompts/. Shared utils sends three named choices to the Decision API: next action, assessment and justification. Scout supplies evidence; Signal chooses Continue, Ask or Unsupported.
