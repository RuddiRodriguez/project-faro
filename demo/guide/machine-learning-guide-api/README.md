# Guide — asks one clarification question

Compass calls Guide only when Signal returns Ask. It sends Thread’s question, the missing choice from Signal, and the titles and text of permitted definitions from Scout. Guide calls the model once through the shared utils handler. Compass can pass an explicit reply language such as `en` or `es`. Otherwise the follow-up prompt asks the model to use the language of the latest user exchange. There is no language detector. It asks about that choice; it does not select an indicator or answer the operational question.

Start from the demo folder:

```sh
venv/bin/python -m uvicorn guide_api.infer:app --port 8006
```

Compass uses `FARO_GUIDE_URL` to override the address. The route is `POST /v1/followup`. On Ask, Compass returns `followup.followup_text`. Continue and Unsupported return `followup: null`; failure to generate a requested question returns an error.

## Implementation

Guide builds the conversation from Signal’s missing choice and Scout’s evidence, calls shared utils and parses the Pydantic-defined response. It returns the follow-up question and short explanation summaries.

## Maria’s two turns

Ask Compass which cranes performed badly at North Terminal last month. When Compass returns a follow-up, show Maria its exact text. On her next request, send the original question and Guide’s actual follow-up in the conversation and her new message as the question. Thread then rewrites the complete request. The demo caller supplies this history; Guide does not store it.
