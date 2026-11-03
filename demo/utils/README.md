# Original utils used by the Faro demo

The demo now uses original utils classes and interfaces, not the previous `faro_utils` wrappers.

Source: `/Users/ruddigarcia/Projects/utils`, `master` commit `a05874ec15ee8debfbc9fbe2f69b766bad9b93ec`.

Thread retains its original chat and structured-output path. For Signal, the decision conversation, prediction result and Decisions request method are from the utils checkout used by Semantica (`47f250a58e0f123c477f35b570abfe15731b1ae0`). Decisions uses Semantica’s options check and dispatch inside the original error-handling block. Only ordinary chat uses the existing intelligence-level resolver. The source manifest records both revisions.

## What is included

- Original `StructuredOutput`, including `name`, `json_schema`, `strict`, `description` and `to_api_input()`.
- Original `LLMHandler(llm_client=...)` and its `predict()` → `chat_predict()` flow.
- Original Conversation, Message, SystemMessage, UserMessage and AssistantMessage classes.
- Original intelligence levels, `.settings` property and resolver.
- Original `PredictOutput`, `AssistantFunction.parsed_arguments`, success checks and token-usage objects.
- Original OpenAiClient constructor and chat methods, including the Responses API handling.

The manifest lists each selected file or definition. Message/tool support classes are included because the original chat classes import them. The complete utils repository is not included.

## Precisely what differs from the source tree

The demo includes only the required files, with the chat subset and import adjustments documented below:

1. `openai_client/openai_consts.py`: only constants/classes used by the copied code, with each selected definition unchanged.
2. `openai_client/openai_client.py`: original class through `chat_predict()`, with all retained method bodies unchanged. Imports used only by omitted embedding, transcription, image-generation and job methods are excluded.
3. `llms/llm_handler.py`: original class unchanged; postponed annotations and a type-only Bedrock client import avoid installing the Bedrock runtime. Original Bedrock model constants and exception classes remain because the original types/settings reference them.

Cloud secret lookup, Bedrock execution and unrelated utils features are outside this demo. The original constructor is used with `explicit_api_key`, not cloud secrets. No new prediction/result/provider wrapper has been introduced.

`SOURCE_MANIFEST.json` records paths, hashes and the pinned commit. Tests compare exact copies byte-for-byte and retained class/method definitions against that commit. They also check handler forwarding and intelligence-level resolution.

## Thread's call

```python
llm_client = OpenAiClient(api_key_secret_name=None, explicit_api_key=api_key)
llm_handler = LLMHandler(llm_client=llm_client)

chat_prediction = llm_handler.predict(
    conversation=conversation,
    structured_output=StandaloneQueryPrompt.STRUCTURED_OUTPUT,
    timeout=30,
    enable_auto_fix_json=False,
)
```

Thread supplies an intelligence level on the conversation, not a model name in the prompt. The original resolver selects model settings for the client. The API creates OpenAiClient directly and passes it to LLMHandler. Bedrock is not implemented or tested in this demo.

Pydantic defines the request schema in Thread:

```python
STRUCTURED_OUTPUT = StructuredOutput(
    name="rewritten_question",
    json_schema=RewrittenQuestion.model_json_schema(),
    strict=True,
)
```

Original utils translates that wrapper into the provider request and returns `assistant_tools[0].parsed_arguments`. Thread's explicit Japan-style parse method validates those arguments with `RewrittenQuestion.model_validate(...)`.

The original client defaults and error behavior are retained. The demo call sets a 30-second timeout and disables JSON auto-repair. The previous custom adapter's 600-token limit, `store=False` override and elapsed-time result wrapper are no longer added. SDK retry count remains the original constructor default of zero; original policy-specific retry handling remains intact.

## Tests

From the demo folder:

```sh
venv/bin/python -m unittest discover -s utils/tests -v
```

Source-comparison tests need the original local repository and the pinned commit. Running the demo itself does not: imported code lives inside this folder.
