# Scout — finds relevant company definitions

Preparation embeds each company document once with the multilingual E5 encoder and the passage: prefix. Each company has its own saved FAISS index and document-reference file. Questions use the query: prefix; only the question is embedded at request time.

The included knowledge_search package validates input, builds the search request and filters hits by score. The local search client preserves the AWS request/result format while searching permitted index rows locally. Scout loads the matching definition text and source references.

From demo/, prepare the model and indexes:

    python scripts/prepare_scout_model.py

To reuse compatible weights, pass --weights /path/to/weights. Rebuild the indexes and restart after changing definitions or weights. The model stays loaded while the service runs. The console starts Scout with the other services.
