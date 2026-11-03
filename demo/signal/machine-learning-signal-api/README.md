# Signal — decides what happens next

Compass calls Signal after Scout. It sends the rewritten question, matching approved definitions, permitted terminal names and the company’s supported-tasks text from Library. In the current demo, that text comes from each company’s approved `supported-tasks.md`.

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

## Reuse

The predictor delegates to `quality/classifier.py`. Decision instructions and rules live under `predictor_files/`; the classifier constructs the utils handler and uses Semantica’s original `classify` method. Japan supplies the service structure: build the conversation, predict through utils, then parse the result. Semantica’s Confluence classifier supplies the call pattern: a named choice in a DecisionsConversation, through LLMHandler to OpenAiClient. One choice carries both the route and, for Ask, the missing detail. Scout’s matches are evidence, not decisions. Signal uses the same Decisions model as Confluence; no chat-model substitute is used.

To exercise the real services including paid OpenAI calls: `FARO_RUN_LIVE_TESTS=1 venv/bin/python -m unittest discover -s compass/machine-learning-compass-api/tests -v`.
