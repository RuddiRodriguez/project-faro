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

## Reuse

Same API → endpoint → predictor layout as the existing demo services and Japan. API and library input/output classes remain separate Pydantic classes.

Thread follows Japan’s `followup/generator.py` pattern: `_build_conversation()` creates the original utils `Conversation`, formats `USER_MESSAGE`, and adds an original `UserMessage`. The prompt holds the original `StructuredOutput` wrapper with `json_schema=RewrittenQuestion.model_json_schema()`. No `response_model` field is added.

`LLMHandler(llm_client=...)` calls the original client’s `chat_predict()`. Thread’s `_parse_chat_prediction_output()` checks `is_success`, reads `assistant_tools[0].parsed_arguments`, and validates those arguments with the Pydantic `RewrittenQuestion` class. Pydantic therefore both defines the request schema and checks required fields/types/non-empty text. No model dump or invented prediction object is used in this flow.

The API loads the saved key, chooses the configured client and maps request/response fields explicitly, following Japan. The original utils snapshot and exact import-only/subset changes are documented in `demo/utils/README.md`.

Rewriting instructions are adapted from Luna API branch `luna-v2`, commit `98e81cd9344a214448df0af7e6904445fd499b7b`, file:

`service/infer/luna/luna/workspace/predictor_files/automata/CONVERSATION.json`, `knowledge_query_instructions`.

Reused rules: combine relevant same-subject conversation, preserve ambiguity and scope, preserve exact identifiers and error messages, and do not invent facts. Faro retains the user's language and omits Luna's search, support-form and answering instructions because those belong outside Thread.

The separate rewriting step follows the earlier Luna standalone-question pattern. The original chat utilities come from pinned utils master; see `demo/utils/README.md`. This is a new combination of existing patterns, not the whole Luna v2 runtime.

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
