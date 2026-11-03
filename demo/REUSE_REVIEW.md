# Faro component structure

The demo separates API inputs and outputs from each service's library inputs and outputs. Endpoints convert between the two. Shared model utilities handle provider calls, structured responses, retries and saved call summaries.

- Compass coordinates service calls and saves each turn.
- Thread rewrites the question with relevant clarification replies.
- Scout searches company indexes through the included knowledge_search package.
- Signal uses named choices in one Decision API call.
- Guide asks the missing clarification question.
- Bridge reads permitted sources; Shield verifies the evidence.
- Voice presents supported findings and document links.

Prompts use role, objective, initial analysis, final reasoning and response sections. Named user-message templates and Pydantic schemas live beside each prompt.

The reference proposal links only to code in this repository. Utility-file checksums are recorded in utils/SOURCE_MANIFEST.json and checked by the local tests.

See the root README for supported sources, permissions and current limits.
