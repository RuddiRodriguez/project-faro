# Voice — explains Shield’s result

Compass calls Voice after Shield. It sends the agreed question, Shield’s decision, the reply language (if specified), and the matching company definition when available.

- **Verified findings:** Voice displays the wording checked by Shield, its evidence sources and any notice of a partial answer. It makes no extra wording call.
- **Single read without findings:** Voice asks the model to phrase the checked result in the user’s language. Python fills in names, dates, ranks and values from Shield. Ties keep their shared rank; a missing rate stays missing. The response includes the approved definition and the source references. Compass keeps the supporting record IDs in its evidence.
- **Withheld:** Without a ranking, Voice returns the reason. With no explicit language preference, or with English requested, it returns the checked reason directly. An explicit preference for another language requests translation of the reason only. Voice does not detect a language. Known company names are inserted after translation.
- **Fallback:** If the wording call fails or drops or changes a fact placeholder, Voice returns the original English rendering. The response marks this as fallback. Placeholder checks protect the supplied values; they do not independently verify the meaning of every word in a translation.

The model uses the demo utils LLMHandler and a Pydantic structured response, following Guide. Voice does not call a database, classify the question or recompute the result.

From demo:

    venv/bin/python -m uvicorn voice_api.infer:app --port 8009
    FARO_RUN_LIVE_TESTS=1 venv/bin/python -m unittest discover -s voice/machine-learning-voice-api/tests -v

Endpoint: POST /v1/answer. Use FARO_VOICE_URL to select another address. The Compass response has an answer only after a Shield decision; Guide still handles clarification.
