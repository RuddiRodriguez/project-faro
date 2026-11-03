# Thread — combines the question and replies

Thread turns a short reply into a question that can be understood without rereading the conversation. It does not answer, search company documents, decide whether clarification is needed or ask questions itself.

## Example

Request to `POST /v1/rewrite`:

```json
{
  "question": "North Terminal.",
  "conversation": [
    {"role": "user", "content": "Which cranes performed badly last month?"},
    {"role": "assistant", "content": "Which terminal?"}
  ]
}
```

The response's `question` is:

> Which cranes performed badly at North Terminal last month?

The response also contains `used_ai: true`, `model_name`, and the original utils `token_usage` object: prompt/completion tokens and available cache/reasoning details.

Thread preserves "performed badly" because Maria has not chosen its meaning. It preserves "last month" because resolving dates is not this service's job. On later calls, send the conversation so far and the latest reply separately. Thread reconstructs the question again using only relevant details. Topic changes must not inherit unrelated details.

With no previous messages, Thread returns the question unchanged with `used_ai: false` and `model_name: null` and `token_usage: null`. No model call is made.

## Implementation

Thread builds a Conversation through shared utils, formats USER_MESSAGE and parses the structured result with RewrittenQuestion.model_validate. Its prompt preserves user choices, ambiguity, scope and exact identifiers without inventing missing facts. API and library inputs and outputs remain separate.

## Run

From the demo folder, with the key already saved in `.env`:

```sh
cd /Users/ruddigarcia/Projects/assesment/demo
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn thread_api.infer:app --host 127.0.0.1 --port 8003
```

The API creates an OpenAI client directly and passes it to the original utils handler.

```sh
curl http://127.0.0.1:8003/v1/rewrite \
  -H 'Content-Type: application/json' \
  -d '{"question":"North Terminal.","conversation":[{"role":"user","content":"Which cranes performed badly last month?"},{"role":"assistant","content":"Which terminal?"}]}'
```

## Current boundary

Thread is implemented as a separate service. Compass now calls Gate, Library and Thread through their APIs and returns Thread’s result in `rewrite`. Thread does not store conversations or check who owns them. Its caller must supply only the relevant user's current conversation. The local demo endpoint is not an authenticated public service.

Incomplete, refused or invalid AI output produces a 502 response rather than a fabricated rewritten question.

## Checks

No-cost checks:

```sh
venv/bin/python -m unittest discover -s thread/machine-learning-thread-api/tests -v
```

Real HTTP and OpenAI check (six paid model calls):

```sh
venv/bin/python scripts/check_thread_live.py
```

This starts Thread on a temporary local port, checks first question, terminal clarification, indicator clarification, topic change, terminal correction, a retail-region reply and a software-error reply, then stops the server. Actual results and usage are saved in `local_data/thread_live_check.json`. These bounded checks are not a full quality evaluation.


After Signal returns Continue, Compass calls POST /v1/ranking on Thread. This separate model task turns the agreed question into a measure, locations, members, dates and order using only permitted choices. A rewrite with several possible referents returns them as unclear_references; Signal asks rather than selecting one. No entity recognizer is required for these examples.
