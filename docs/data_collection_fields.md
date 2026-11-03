# Faro data collection: fields and origins

Product proposal: SQL. Local demo: Parquet, using the same named columns.

## conversations

| Column | Type | Comes from |
|---|---|---|
| conversation_id | TEXT | Compass generates a UUID on the first message; later requests return that same ID. |
| company_id | TEXT | Gate: company on the signed-in demo account. |
| user_id | TEXT | Gate: verified account that started the conversation. |
| original_question | TEXT | First user message in supplied history, otherwise the first request.question. |
| created_at | TIMESTAMP | Compass UTC clock when the conversation starts. |
| access_json | JSON | Gate result at creation: user_id, company_id, permitted_scope_ids and permission_version from users.json. |
| initial_history_json | JSON | Only role and content supplied by the caller when starting a conversation; not independently verified history. |

## model_calls

| Column | Type | Comes from |
|---|---|---|
| turn_id | TEXT | Compass turn ID, passed to the service with the request. |
| call_id | TEXT | Shared utils generates one ID per logical model call; retries keep it. |
| service | TEXT | Name of the service making the model call. |
| started_ns | INTEGER | Service clock at the start of the logical call, Unix nanoseconds. |
| explanations_json | JSON | Model response: brief initial_analysis and reasoning per attempt, with its attempt number. Not private chain of thought. |
| outcomes_json | JSON | One outcome per provider attempt, in order; in_progress until the provider returns. |

## turns

| Column | Type | Comes from |
|---|---|---|
| turn_id | TEXT | Compass UUID for this individual message. |
| conversation_id | TEXT | Foreign key to the owned conversation selected by Compass after Gate checks access. |
| turn_number | INTEGER | Compass: previous saved turn count plus one, under the conversation lock. |
| message | TEXT | Exact current user message from request.question. |
| language | TEXT | Optional reply-language preference from the request, not an inferred language. |
| created_at | TIMESTAMP | Compass UTC clock before processing this turn. |
| status | TEXT | Compass: started or failed; otherwise Shield's status or the final next-action decision. |
| decision_source | TEXT | Compass identifies Signal or Bridge as the producer of the final action. |
| plan_json | JSON | Bridge's proposed source read, when available; null for a clarification before reading. |
| response_json | JSON | Service outputs collected by Compass; individual fields are listed in the field guide. |
| cache_events_json | JSON | Compass lookup events for this turn: service, collection, key, fresh/cache/rejected and producing turn. |
| model_attempts_tracked | INTEGER | Compass: tracking enabled for this turn. Older turns have no counts. |
| error | TEXT | Service, endpoint and failure type when a service call fails; otherwise the exception class. No invented substitute response. |
| elapsed_ms | INTEGER | Compass monotonic timer: milliseconds from turn processing start to outcome. Not an invoice. |
| cache_version | TEXT | Compass fingerprint of the deployed cache policy, service code and settings. |

## field_origins

| Column | Type | Comes from |
|---|---|---|
| table_name | TEXT | Declared Faro table whose field is described. |
| field_path | TEXT | Column name, or nested path in its saved JSON value; [] denotes an item. |
| source | TEXT | Description defined in the Faro schema or recorded service output contract. |

## ai_cache

| Column | Type | Comes from |
|---|---|---|
| cache_key | TEXT | Compass hash of company, permissions, company information, policy version, service and exact inputs; AI keys also include the user. |
| company_id | TEXT | Gate: the company permitted to reuse this entry. |
| service | TEXT | Compass identifies the producing service call. |
| version | TEXT | Compass cache policy fingerprint when the entry was written. |
| cached_value_json | JSON | Typed output of the named AI service, or Bridge facts independently verified by Shield. |
| expires_at | TIMESTAMP | Compass UTC save time plus 120 days. |
| produced_by_turn | TEXT | Foreign key to the turn that actually produced this value; absent if an older record did not save it. |

## data_cache

| Column | Type | Comes from |
|---|---|---|
| cache_key | TEXT | Compass hash of company, permissions, company information, policy version, service and exact inputs; AI keys also include the user. |
| company_id | TEXT | Gate: the company permitted to reuse this entry. |
| service | TEXT | Compass identifies the producing service call. |
| version | TEXT | Compass cache policy fingerprint when the entry was written. |
| cached_value_json | JSON | Typed output of the named AI service, or Bridge facts independently verified by Shield. |
| expires_at | TIMESTAMP | Compass UTC save time plus 120 days. |
| produced_by_turn | TEXT | Foreign key to the turn that actually produced this value; absent if an older record did not save it. |

## Values inside saved responses

| Field | Comes from |
|---|---|
| cache_events_json[].collection | Compass: selected cache table and service call. |
| cache_events_json[].service | Compass: selected cache table and service call. |
| cache_events_json[].key | Compass cache lookup fingerprint; joins to cache_key in the named table. |
| cache_events_json[].result_source | Compass: fresh call, valid cache hit, or data rejected by Shield. |
| cache_events_json[].produced_by_turn | Saved entry's originating turn; for a new entry, the current turn ID. |
| response_json.question | User: exact current message. |
| response_json.conversation_id | Compass: same IDs as this row and its parent. |
| response_json.turn_id | Compass: same IDs as this row and its parent. |
| response_json.rewrite | Compass stores only the services reached on this route; see child fields. |
| response_json.search | Compass stores only the services reached on this route; see child fields. |
| response_json.decision | Compass stores only the services reached on this route; see child fields. |
| response_json.followup | Compass stores only the services reached on this route; see child fields. |
| response_json.evidence | Compass stores only the services reached on this route; see child fields. |
| response_json.verification | Compass stores only the services reached on this route; see child fields. |
| response_json.answer | Compass stores only the services reached on this route; see child fields. |
| response_json.rewrite.question | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| response_json.rewrite.unclear_references | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| response_json.rewrite.used_ai | Thread: whether the original rewrite used AI and which model answered. |
| response_json.rewrite.model_name | Thread: whether the original rewrite used AI and which model answered. |
| response_json.rewrite.token_usage | Provider usage for the original prediction, not a new charge on a cache hit. |
| response_json.rewrite.token_usage.prompt_tokens | OpenAI usage returned to Thread through utils; absent when not reported. |
| response_json.rewrite.token_usage.completion_tokens | OpenAI usage returned to Thread through utils; absent when not reported. |
| response_json.rewrite.token_usage.prompt_tokens_details | OpenAI usage returned to Thread through utils; absent when not reported. |
| response_json.rewrite.token_usage.completion_tokens_details | OpenAI usage returned to Thread through utils; absent when not reported. |
| response_json.rewrite.token_usage.prompt_tokens_details.audio_tokens | OpenAI prompt-token breakdown on the original model call. |
| response_json.rewrite.token_usage.prompt_tokens_details.cached_tokens | OpenAI prompt-token breakdown on the original model call. |
| response_json.rewrite.token_usage.prompt_tokens_details.cache_write_tokens | OpenAI prompt-token breakdown on the original model call. |
| response_json.rewrite.token_usage.completion_tokens_details.accepted_prediction_tokens | OpenAI completion-token breakdown on the original model call. |
| response_json.rewrite.token_usage.completion_tokens_details.audio_tokens | OpenAI completion-token breakdown on the original model call. |
| response_json.rewrite.token_usage.completion_tokens_details.reasoning_tokens | OpenAI completion-token breakdown on the original model call. |
| response_json.rewrite.token_usage.completion_tokens_details.rejected_prediction_tokens | OpenAI completion-token breakdown on the original model call. |
| response_json.search.query | Scout: search input from Thread and permitted matches from its company index. |
| response_json.search.matches | Scout: search input from Thread and permitted matches from its company index. |
| response_json.search.matches[].document_id | Scout: passage from a permitted connected source, with its location and version. |
| response_json.search.matches[].title | Scout: passage from a permitted connected source, with its location and version. |
| response_json.search.matches[].text | Scout: passage from a permitted connected source, with its location and version. |
| response_json.search.matches[].source | Scout: passage from a permitted connected source, with its location and version. |
| response_json.search.matches[].version | Scout: passage from a permitted connected source, with its location and version. |
| response_json.search.matches[].file_reference | Scout: index source reference and relevance score, not proof of correctness. |
| response_json.search.matches[].score | Scout: index source reference and relevance score, not proof of correctness. |
| response_json.decision.action | Signal's classification or Bridge's clarification/stop; see decision_source. |
| response_json.decision.missing_choice | Signal's classification or Bridge's clarification/stop; see decision_source. |
| response_json.followup.followup_text | Guide: clarification generated for the missing choice. |
| response_json.followup.initial_analysis | Guide: clarification generated for the missing choice. |
| response_json.followup.reasoning | Guide: clarification generated for the missing choice. |
| plan_json.source | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.scope_ids | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.member_ids | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.group | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.start | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.end_exclusive | Bridge model proposes the permitted source and bounded read through utils. |
| plan_json.expression | Bridge model proposes the permitted source and bounded read through utils. |
| response_json.verification.status | Shield checks source records and whether the read answers the question. |
| response_json.verification.reason | Shield checks source records and whether the read answers the question. |
| response_json.verification.facts | Shield checks source records and whether the read answers the question. |
| response_json.evidence.question | Compass supplies the question and Gate company. |
| response_json.evidence.company_id | Compass supplies the question and Gate company. |
| response_json.evidence.status | Bridge returns read status, explanation and selected read. |
| response_json.evidence.reason | Bridge returns read status, explanation and selected read. |
| response_json.evidence.read | Bridge returns read status, explanation and selected read. |
| response_json.evidence.read.source | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.scope_ids | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.member_ids | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.group | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.start | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.end_exclusive | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.read.expression | Bridge model produces the read, checked against permitted sources. |
| response_json.evidence.data_version | Bridge reads the version, source, unit and dates from company records. |
| response_json.evidence.source | Bridge reads the version, source, unit and dates from company records. |
| response_json.evidence.unit | Bridge reads the version, source, unit and dates from company records. |
| response_json.evidence.period | Bridge reads the version, source, unit and dates from company records. |
| response_json.evidence.supporting | Additional replayable reads from the same answer, in evidence ID order. |
| response_json.evidence.catalogue_version | Fingerprint of the company catalogue visible for this request. |
| response_json.evidence.findings | Bridge proposes findings; Shield returns only the supported ones. |
| response_json.evidence.findings[].text | Reviewed finding and citations: 0 for catalogue, positive IDs for reads. |
| response_json.evidence.findings[].evidence_ids | Reviewed finding and citations: 0 for catalogue, positive IDs for reads. |
| response_json.evidence.record_ids | Identifiers of the contributing source records and the pandas result. |
| response_json.evidence.rows | Identifiers of the contributing source records and the pandas result. |
| response_json.evidence.rows[].member | Checked pandas result; member is present only for grouped output. |
| response_json.evidence.rows[].scope_name | Checked pandas result; member is present only for grouped output. |
| response_json.evidence.rows[].asset_type | Checked pandas result; member is present only for grouped output. |
| response_json.evidence.rows[].activity_date | Checked pandas result; member is present only for grouped output. |
| response_json.evidence.rows[].value | Checked pandas result; member is present only for grouped output. |
| response_json.verification.facts.question | Compass supplies the question and Gate company. |
| response_json.verification.facts.company_id | Compass supplies the question and Gate company. |
| response_json.verification.facts.status | Bridge returns read status, explanation and selected read. |
| response_json.verification.facts.reason | Bridge returns read status, explanation and selected read. |
| response_json.verification.facts.read | Bridge returns read status, explanation and selected read. |
| response_json.verification.facts.read.source | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.scope_ids | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.member_ids | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.group | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.start | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.end_exclusive | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.read.expression | Bridge model produces the read, checked against permitted sources. |
| response_json.verification.facts.data_version | Bridge reads the version, source, unit and dates from company records. |
| response_json.verification.facts.source | Bridge reads the version, source, unit and dates from company records. |
| response_json.verification.facts.unit | Bridge reads the version, source, unit and dates from company records. |
| response_json.verification.facts.period | Bridge reads the version, source, unit and dates from company records. |
| response_json.verification.facts.supporting | Additional replayable reads from the same answer, in evidence ID order. |
| response_json.verification.facts.catalogue_version | Fingerprint of the company catalogue visible for this request. |
| response_json.verification.facts.findings | Bridge proposes findings; Shield returns only the supported ones. |
| response_json.verification.facts.findings[].text | Reviewed finding and citations: 0 for catalogue, positive IDs for reads. |
| response_json.verification.facts.findings[].evidence_ids | Reviewed finding and citations: 0 for catalogue, positive IDs for reads. |
| response_json.verification.facts.record_ids | Identifiers of the contributing source records and the pandas result. |
| response_json.verification.facts.rows | Identifiers of the contributing source records and the pandas result. |
| response_json.verification.facts.rows[].member | Checked pandas result; member is present only for grouped output. |
| response_json.verification.facts.rows[].scope_name | Checked pandas result; member is present only for grouped output. |
| response_json.verification.facts.rows[].asset_type | Checked pandas result; member is present only for grouped output. |
| response_json.verification.facts.rows[].activity_date | Checked pandas result; member is present only for grouped output. |
| response_json.verification.facts.rows[].value | Checked pandas result; member is present only for grouped output. |
| response_json.answer.status | Operational answers use Shield's decision. Unsupported data requests may be withheld without a ranking. |
| response_json.answer.text | Voice displays Shield-reviewed findings, a direct limitation, or checked legacy wording. |
| response_json.answer.mode | Voice displays Shield-reviewed findings, a direct limitation, or checked legacy wording. |
| response_json.answer.sources | Voice copies Bridge's operational source and Scout's matched source passage and reference. |
| response_json.answer.definition | Voice copies Bridge's operational source and Scout's matched source passage and reference. |
| response_json.rewrite.initial_analysis | Service model response: brief factual assessment and decision justification. |
| response_json.rewrite.reasoning | Service model response: brief factual assessment and decision justification. |
| response_json.decision.initial_analysis | Service model response: brief factual assessment and decision justification. |
| response_json.decision.reasoning | Service model response: brief factual assessment and decision justification. |
