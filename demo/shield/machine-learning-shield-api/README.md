# Shield — checks the answer against the records

Shield reopens the permitted sources, repeats each of Bridge's reads and compares the evidence, including source version and contributing records. Through utils it checks that the meaning of the read matches the user's question. It checks that the catalogue is unchanged and reviews each finding against the evidence IDs it cites. Only supported findings are displayed; if none remain, the answer is withheld. A semantic check is a model judgment, not a proof about the quality of the original source.

Run from the demo folder:

    venv/bin/python -m uvicorn shield_api.infer:app --port 8008
    venv/bin/python -m unittest discover -s shield/machine-learning-shield-api/tests -v

Compass calls POST /v1/verify. FARO_SHIELD_URL changes the service address; FARO_DATA_PATH selects the dataset.
