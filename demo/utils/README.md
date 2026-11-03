# Faro shared model utilities

Model services build a Conversation and call LLMHandler.predict. The handler calls the configured provider, records attempts and retries temporary failures up to three attempts in the same call.

StructuredOutput holds name, json_schema, strict and description. Prompts define their schema using Pydantic. Services parse assistant_tools[0].parsed_arguments and validate the result with the prompt's Pydantic class.

Ordinary chat calls use the shared intelligence-level settings. Decision calls use the configured Decision API model and named choices. Provider model identifiers remain unchanged because they are required by the API.

The utilities also record short initial_analysis and reasoning summaries per model call. SOURCE_MANIFEST.json records local file checksums for integrity checks. Run the tests from demo/:

    python -m unittest discover -s utils/tests -v
