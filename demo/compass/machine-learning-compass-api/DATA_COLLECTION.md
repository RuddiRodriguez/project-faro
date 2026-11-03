# Faro’s data collection

**Proposal: Faro owns SQL tables. Demo: pandas reads and writes the same columns in Parquet.** Neither choice dictates how a client stores operational records. [Proposed SQL schema](../../../docs/data_collection_schema.sql).

| Table | Contents |
|---|---|
| conversations | Verified company and user, first question, access snapshot, and initial history supplied by the caller. |
| turns | One user message linked to its conversation, ordered by turn number. Stores the decision, plan, sources, Shield checks, Voice answer or failure, elapsed time and cache events. |
| ai_cache | Successful AI results. Exact inputs, user, permissions, company material, model/code policy and version must still match. |
| data_cache | Only independently verified rankings. A hit skips Bridge, but not Gate or Shield. If Shield rejects stale data, Compass discards the entry and reads fresh records. |
| field_origins | Every column’s producer and the meaning of nested service fields. Each cache entry links to the turn that produced it. Each lookup on a turn records its key, service and fresh/cache/rejected outcome. |

Each company has its own folder under `demo/local_data/data_collection/` (override with `FARO_COLLECTION_PATH`). Each row has a stable filename; pandas writes each changed row to a temporary file, then replaces it atomically. Conversations are locked independently while a turn is running. This is a single-host demo, not a transactional multi-host database. Structured service outputs use JSON in named columns, not as the storage format. Earlier exports without an observed producing turn keep that value null.

Read the actual tables from the demo folder:

```python
import pandas as pd
root = "local_data/data_collection/cedar"
turns = pd.read_parquet(f"{root}/turns")
print(turns[["conversation_id", "turn_number", "message", "elapsed_ms"]])
print(pd.read_parquet(f"{root}/field_origins").to_string(index=False))
```

Start with `{"user_id":"maria","question":"Which cranes performed badly at North Terminal last month?"}`. Copy the returned `conversation_id`. Send `{"user_id":"maria","conversation_id":"<returned UUID>","question":"Highest downtime."}`. Compass loads the history for that account. Without an ID it starts a new conversation. A changed access snapshot prevents reopening the old conversation. To view all turns in readable form: `venv/bin/python scripts/export_conversation.py harbor <conversation_id>`.

**Japan reuse:** [API fetch, predict, save and upload](</Users/ruddigarcia/Projects/machine-learning-japan-api/infer/src/endpoints/predict_endpoint.py:111>) and [cache key, version and 120-day expiry](</Users/ruddigarcia/Projects/machine-learning-japan-api/infer/src/dal.py:29>). Only a new question with no conversation ID or supplied history may read or write the application caches. Replies are still saved in order, but all their service calls run fresh. After Gate and Library, on an opening question Compass checks for a valid matching result before calling the service. Successful results can be reused. Failed calls are logged, not cached. Hits on Signal, Thread’s ranking call, Guide or AI-written Voice answers skip a model call. A Bridge hit skips fetching the ranking again, but Shield still reads the source. A cached Thread token count describes the original call, not new usage.

Bump `FARO_CACHE_VERSION` for configuration changes on separately deployed services. The local service policy and model settings are also fingerprinted. No monetary savings are inferred from timing or historical token counts. Requests before collection existed cannot be reconstructed unless recorded elsewhere.
