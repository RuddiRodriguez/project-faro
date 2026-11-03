# Scout — finds relevant company definitions

Compass sends Thread’s question and the approved document IDs Library released for that person. Scout searches only those IDs within the verified company. It returns up to three definitions with their title, text, source, version, local file reference and score. Finding a definition does not tell us which indicator the user intended or which cranes performed badly.

## Run from the demo folder

Install the root requirements in the shared environment. Run `venv/bin/python scripts/prepare_scout_model.py` to copy Luna’s E5 model and tokenizer from the local checkout and build each company’s FAISS index. Use `--weights /path/to/weights` for another checkout. On macOS the script configures FAISS to use PyTorch’s OpenMP library inside the demo environment; its bundled original is kept as a backup. Then start Scout:

```sh
venv/bin/python -m uvicorn scout_api.infer:app --port 8004
```

Preparation reads the approved company documents. Luna’s E5 encoder turns each title and definition into a vector once, using the `passage:` prefix. Each company gets a FAISS file plus a JSON file linking its rows to the source documents under `local_data/scout_indexes/`. Rebuild and restart after changing definitions or weights.

Scout loads the saved files at startup. At search time it embeds only the question, using the same local E5 weights with the `query:` prefix. FAISS searches the permitted rows of that company’s index. An English and a Spanish question can therefore find the same English definition. Scout requires no network connection; Thread’s optional OpenAI rewrite remains a separate service.

## What comes from Luna

Preparation uses the original Luna Retrieval, Embedding and FaissIndex modules. At query time the local client uses a retrieval class with Luna’s embedder interface and normalization, loading the saved index and restricting candidate rows before ranking. See the [reuse review](../../REUSE_REVIEW.md) for the exact source and necessary differences.

## What comes from Nemo

The files under `infer/scout/nemo/retrieval` and the validation messages are copied unchanged from machine-learning-nemo commit `825f5d64cabd2f1630a7574502c13e42ae5b436b`. Its predictor constructor and search method are copied unchanged; indexing and deletion are outside Scout. Nemo validates the input, builds the Bedrock Retrieve request, applies the minimum score and returns source references. Scout loads the approved text for each reference.

The local client implements the text retrieval request Scout actually sends: a knowledge base ID, query text, result limit and an AssetId inclusion filter. Its result has the Bedrock text, S3 location, metadata and score format. The S3-shaped references identify local documents; no bucket is created. Scores are cosine similarities between unit vectors. The 0.74 E5 cutoff separates the tested crane and unrelated hotel examples in English and Spanish; it is a demo setting, not a calibrated confidence level. This is not an emulator of other Bedrock operations or a reproduction of AWS ranking.

Run the local retrieval tests with `venv/bin/python -m unittest discover -s scout/machine-learning-scout-api/tests`. The Compass HTTP tests exercise Scout as a separate service.
