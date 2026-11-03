# Scout — finds relevant connected source material

Scout lists sources through Connector using Gate's company and access scope. It indexes field names and text PDF passages with multilingual E5 and stores a FAISS index keyed by company, permissions, source versions and model version. No prepared company definitions are loaded.

On first search, or after a source changes, Scout builds the index. On repeat searches it embeds only the question. The encoder stays loaded in the service. Production should build indexes when data is connected rather than making the first user wait.

The included knowledge_search code keeps the AWS Retrieve request/result shape. The local client supplies matches from the permitted saved index. Scout returns passages with source references and versions, plus the full permitted source list. Matching text guides Bridge; it does not establish an operational answer.

From demo/, run `python scripts/prepare_scout_model.py` to prepare the model. Use `--weights /path/to/weights` to copy compatible weights. Source indexing is automatic.
