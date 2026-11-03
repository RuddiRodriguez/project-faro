# Faro data collection: where each field comes from

SQL design and demo share these field names. For a cache hit, the cache event points to the original producing turn. Provider token counts on a cached rewrite describe the original call.

## conversations

| Field | Source |
|---|---|
| `conversation_id` | Compass generates a UUID on the first message; later requests return that same ID. |
| `company_id` | Gate: company on the signed-in demo account. |
| `user_id` | Gate: verified account that started the conversation. |
| `original_question` | First user message in supplied history, otherwise the first request.question. |
| `created_at` | Compass UTC clock when the conversation starts. |
| `access_json` | Gate result at creation: user_id, company_id, permitted_scope_ids and permission_version from users.json. |
| `initial_history_json` | Only role and content supplied by the caller when starting a conversation; not independently verified history. |
| `access_json.user_id` | Gate reads this field from the saved account in users.json. |
| `access_json.company_id` | Gate reads this field from the saved account in users.json. |
| `access_json.permitted_scope_ids` | Gate reads this field from the saved account in users.json. |
| `access_json.permission_version` | Gate reads this field from the saved account in users.json. |
| `initial_history_json[].role` | Caller-supplied conversation message on the opening request. |
| `initial_history_json[].content` | Caller-supplied conversation message on the opening request. |

## turns

| Field | Source |
|---|---|
| `turn_id` | Compass UUID for this individual message. |
| `conversation_id` | Foreign key to the owned conversation selected by Compass after Gate checks access. |
| `turn_number` | Compass: previous saved turn count plus one, under the conversation lock. |
| `message` | Exact current user message from request.question. |
| `language` | Optional reply-language preference from the request, not an inferred language. |
| `created_at` | Compass UTC clock before processing this turn. |
| `status` | Compass: started or failed; otherwise Shield's status or the final next-action decision. |
| `decision_source` | Compass identifies Signal or Thread.ranking as the producer of the final action. |
| `plan_json` | Thread.ranking output: selected company definition, scopes, group, members, dates and order, or reason not to proceed. |
| `response_json` | Service outputs collected by Compass; individual fields are listed in the field guide. |
| `cache_events_json` | Compass lookup events for this turn: service, collection, key, fresh/cache/rejected and producing turn. |
| `error` | Exception class caught by Compass after access verification. No invented substitute response. |
| `elapsed_ms` | Compass monotonic timer: milliseconds from turn processing start to outcome. Not an invoice. |
| `cache_version` | Compass fingerprint of the deployed cache policy, service code and settings. |
| `cache_events_json[].collection` | Compass: selected cache table and service call. |
| `cache_events_json[].service` | Compass: selected cache table and service call. |
| `cache_events_json[].key` | Compass cache lookup fingerprint; joins to cache_key in the named table. |
| `cache_events_json[].result_source` | Compass: fresh call, valid cache hit, or data rejected by Shield. |
| `cache_events_json[].produced_by_turn` | Saved entry's originating turn; for a new entry, the current turn ID. |
| `response_json.question` | User: exact current message. |
| `response_json.conversation_id` | Compass: same IDs as this row and its parent. |
| `response_json.turn_id` | Compass: same IDs as this row and its parent. |
| `response_json.rewrite` | Compass stores only the services reached on this route; see child fields. |
| `response_json.search` | Compass stores only the services reached on this route; see child fields. |
| `response_json.decision` | Compass stores only the services reached on this route; see child fields. |
| `response_json.followup` | Compass stores only the services reached on this route; see child fields. |
| `response_json.evidence` | Compass stores only the services reached on this route; see child fields. |
| `response_json.verification` | Compass stores only the services reached on this route; see child fields. |
| `response_json.answer` | Compass stores only the services reached on this route; see child fields. |
| `response_json.rewrite.question` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `response_json.rewrite.unclear_references` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `response_json.rewrite.intent` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `response_json.rewrite.current_request` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `response_json.rewrite.current_request.task` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.subjects` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.scope` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.period` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.measure` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.order` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.current_request.conditions` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `response_json.rewrite.used_ai` | Thread: whether the original rewrite used AI and which model answered. |
| `response_json.rewrite.model_name` | Thread: whether the original rewrite used AI and which model answered. |
| `response_json.rewrite.token_usage` | Provider usage for the original prediction, not a new charge on a cache hit. |
| `response_json.rewrite.token_usage.prompt_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `response_json.rewrite.token_usage.completion_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `response_json.rewrite.token_usage.prompt_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `response_json.rewrite.token_usage.completion_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `response_json.rewrite.token_usage.prompt_tokens_details.audio_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.prompt_tokens_details.cached_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.prompt_tokens_details.cache_write_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.completion_tokens_details.accepted_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.completion_tokens_details.audio_tokens` | OpenAI completion-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.completion_tokens_details.reasoning_tokens` | OpenAI completion-token breakdown on the original model call. |
| `response_json.rewrite.token_usage.completion_tokens_details.rejected_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `response_json.search.query` | Scout: search input from Thread and permitted matches from its company index. |
| `response_json.search.matches` | Scout: search input from Thread and permitted matches from its company index. |
| `response_json.search.matches[].document_id` | Scout: approved company document; Compass checks the returned match against Library. |
| `response_json.search.matches[].title` | Scout: approved company document; Compass checks the returned match against Library. |
| `response_json.search.matches[].text` | Scout: approved company document; Compass checks the returned match against Library. |
| `response_json.search.matches[].source` | Scout: approved company document; Compass checks the returned match against Library. |
| `response_json.search.matches[].version` | Scout: approved company document; Compass checks the returned match against Library. |
| `response_json.search.matches[].file_reference` | Scout: index source reference and relevance score, not proof of correctness. |
| `response_json.search.matches[].score` | Scout: index source reference and relevance score, not proof of correctness. |
| `response_json.decision.action` | Signal's classification or Thread.ranking's clarification/stop; see decision_source. |
| `response_json.decision.missing_choice` | Signal's classification or Thread.ranking's clarification/stop; see decision_source. |
| `response_json.followup.proposed_changes[].field` | Guide records exactly what the user would accept. |
| `response_json.followup.proposed_changes[].value` | Guide records exactly what the user would accept. |
| `response_json.followup.followup_text` | Guide: clarification generated for the missing choice. |
| `response_json.followup.proposed_changes` | Guide: clarification generated for the missing choice. |
| `plan_json.status` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `plan_json.reason` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `plan_json.ranking` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `plan_json.selected_definition_id` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `plan_json.ranking.definition_id` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.scope_ids` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.group` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.member_ids` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.start` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.end_exclusive` | Thread chooses from permitted company options; dates use Library's reference date. |
| `plan_json.ranking.order` | Thread chooses from permitted company options; dates use Library's reference date. |
| `response_json.verification.status` | Shield: result of checking the current records; no facts for withheld. |
| `response_json.verification.reason` | Shield: result of checking the current records; no facts for withheld. |
| `response_json.verification.facts` | Shield: result of checking the current records; no facts for withheld. |
| `response_json.evidence.company_id` | Gate company included in Bridge result and confirmed by Shield. |
| `response_json.evidence.status` | Bridge result status and availability reason. |
| `response_json.evidence.reason` | Bridge result status and availability reason. |
| `response_json.evidence.ranking` | Thread ranking passed to Bridge and checked by Shield. |
| `response_json.evidence.ranking.definition_id` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.scope_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.group` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.member_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.start` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.end_exclusive` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.ranking.order` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.evidence.unit` | Library's approved company measure definition used by Bridge. |
| `response_json.evidence.data_version` | Bridge reads company data version and identifies the operational source file. |
| `response_json.evidence.source` | Bridge reads company data version and identifies the operational source file. |
| `response_json.evidence.totals` | Bridge ranks the selected groups; Shield independently checks the member set, figures and order. |
| `response_json.evidence.totals[].asset_id` | Bridge: member identifier and IDs of contributing client source rows. |
| `response_json.evidence.totals[].record_ids` | Bridge: member identifier and IDs of contributing client source rows. |
| `response_json.evidence.totals[].value` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.evidence.totals[].rank` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.evidence.totals[].reason` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.verification.facts.company_id` | Gate company included in Bridge result and confirmed by Shield. |
| `response_json.verification.facts.status` | Bridge result status and availability reason. |
| `response_json.verification.facts.reason` | Bridge result status and availability reason. |
| `response_json.verification.facts.ranking` | Thread ranking passed to Bridge and checked by Shield. |
| `response_json.verification.facts.ranking.definition_id` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.scope_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.group` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.member_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.start` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.end_exclusive` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.ranking.order` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `response_json.verification.facts.unit` | Library's approved company measure definition used by Bridge. |
| `response_json.verification.facts.data_version` | Bridge reads company data version and identifies the operational source file. |
| `response_json.verification.facts.source` | Bridge reads company data version and identifies the operational source file. |
| `response_json.verification.facts.totals` | Bridge ranks the selected groups; Shield independently checks the member set, figures and order. |
| `response_json.verification.facts.totals[].asset_id` | Bridge: member identifier and IDs of contributing client source rows. |
| `response_json.verification.facts.totals[].record_ids` | Bridge: member identifier and IDs of contributing client source rows. |
| `response_json.verification.facts.totals[].value` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.verification.facts.totals[].rank` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.verification.facts.totals[].reason` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `response_json.answer.status` | Operational answers use Shield's decision. Unsupported data requests may be withheld without a ranking. |
| `response_json.answer.text` | Voice: model wording with facts filled by Python, direct reason, or fallback. |
| `response_json.answer.mode` | Voice: model wording with facts filled by Python, direct reason, or fallback. |
| `response_json.answer.sources` | Voice copies Bridge's operational source and Scout's matched Library definition and reference. |
| `response_json.answer.definition` | Voice copies Bridge's operational source and Scout's matched Library definition and reference. |

## field_origins

| Field | Source |
|---|---|
| `table_name` | Declared Faro table whose field is described. |
| `field_path` | Column name, or nested path in its saved JSON value; [] denotes an item. |
| `source` | Description defined in the Faro schema or recorded service output contract. |

## ai_cache

| Field | Source |
|---|---|
| `cache_key` | Compass hash of company, permissions, company information, policy version, service and exact inputs; AI keys also include the user. |
| `company_id` | Gate: the company permitted to reuse this entry. |
| `service` | Compass identifies the producing service call. |
| `version` | Compass cache policy fingerprint when the entry was written. |
| `cached_value_json` | Typed output of the named AI service, or Bridge facts independently verified by Shield. |
| `expires_at` | Compass UTC save time plus 120 days, adapted from Japan's API DAL. |
| `produced_by_turn` | Foreign key to the turn that actually produced this value; absent if an older record did not save it. |
| `cached_value_json[Thread.turn].question` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.turn].unclear_references` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.turn].intent` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.turn].current_request` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.turn].current_request.task` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.subjects` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.scope` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.period` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.measure` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.order` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].current_request.conditions` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.turn].used_ai` | Thread: whether the original rewrite used AI and which model answered. |
| `cached_value_json[Thread.turn].model_name` | Thread: whether the original rewrite used AI and which model answered. |
| `cached_value_json[Thread.turn].token_usage` | Provider usage for the original prediction, not a new charge on a cache hit. |
| `cached_value_json[Thread.turn].token_usage.prompt_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.turn].token_usage.prompt_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.turn].token_usage.prompt_tokens_details.audio_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.prompt_tokens_details.cached_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.prompt_tokens_details.cache_write_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens_details.accepted_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens_details.audio_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens_details.reasoning_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.turn].token_usage.completion_tokens_details.rejected_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].question` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.rewrite].unclear_references` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.rewrite].intent` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.rewrite].current_request` | Thread: wording, unresolved references, reason for this turn, and retained details of the request. |
| `cached_value_json[Thread.rewrite].current_request.task` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.subjects` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.scope` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.period` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.measure` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.order` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].current_request.conditions` | Thread identifies user changes. Other agreed details remain from the previous turn. |
| `cached_value_json[Thread.rewrite].used_ai` | Thread: whether the original rewrite used AI and which model answered. |
| `cached_value_json[Thread.rewrite].model_name` | Thread: whether the original rewrite used AI and which model answered. |
| `cached_value_json[Thread.rewrite].token_usage` | Provider usage for the original prediction, not a new charge on a cache hit. |
| `cached_value_json[Thread.rewrite].token_usage.prompt_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.rewrite].token_usage.prompt_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens_details` | OpenAI usage returned to Thread through utils; absent when not reported. |
| `cached_value_json[Thread.rewrite].token_usage.prompt_tokens_details.audio_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.prompt_tokens_details.cached_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.prompt_tokens_details.cache_write_tokens` | OpenAI prompt-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens_details.accepted_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens_details.audio_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens_details.reasoning_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.rewrite].token_usage.completion_tokens_details.rejected_prediction_tokens` | OpenAI completion-token breakdown on the original model call. |
| `cached_value_json[Thread.ranking].status` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `cached_value_json[Thread.ranking].reason` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `cached_value_json[Thread.ranking].ranking` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `cached_value_json[Thread.ranking].selected_definition_id` | Thread.ranking: agreed choices based on the rewritten question, Library options and Scout matches. |
| `cached_value_json[Thread.ranking].ranking.definition_id` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.scope_ids` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.group` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.member_ids` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.start` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.end_exclusive` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Thread.ranking].ranking.order` | Thread chooses from permitted company options; dates use Library's reference date. |
| `cached_value_json[Signal].action` | Signal's classification before any later Thread.ranking decision. |
| `cached_value_json[Signal].missing_choice` | Signal's classification before any later Thread.ranking decision. |
| `cached_value_json[Guide].proposed_changes[].field` | Guide records exactly what the user would accept. |
| `cached_value_json[Guide].proposed_changes[].value` | Guide records exactly what the user would accept. |
| `cached_value_json[Guide].followup_text` | Guide: clarification generated for the missing choice. |
| `cached_value_json[Guide].proposed_changes` | Guide: clarification generated for the missing choice. |
| `cached_value_json[Voice].status` | Operational answers use Shield's decision. Unsupported data requests may be withheld without a ranking. |
| `cached_value_json[Voice].text` | Voice: model wording with facts filled by Python, direct reason, or fallback. |
| `cached_value_json[Voice].mode` | Voice: model wording with facts filled by Python, direct reason, or fallback. |
| `cached_value_json[Voice].sources` | Voice copies Bridge's operational source and Scout's matched Library definition and reference. |
| `cached_value_json[Voice].definition` | Voice copies Bridge's operational source and Scout's matched Library definition and reference. |

## data_cache

| Field | Source |
|---|---|
| `cache_key` | Compass hash of company, permissions, company information, policy version, service and exact inputs; AI keys also include the user. |
| `company_id` | Gate: the company permitted to reuse this entry. |
| `service` | Compass identifies the producing service call. |
| `version` | Compass cache policy fingerprint when the entry was written. |
| `cached_value_json` | Typed output of the named AI service, or Bridge facts independently verified by Shield. |
| `expires_at` | Compass UTC save time plus 120 days, adapted from Japan's API DAL. |
| `produced_by_turn` | Foreign key to the turn that actually produced this value; absent if an older record did not save it. |
| `cached_value_json[Bridge].company_id` | Gate company included in Bridge result and confirmed by Shield. |
| `cached_value_json[Bridge].status` | Bridge result status and availability reason. |
| `cached_value_json[Bridge].reason` | Bridge result status and availability reason. |
| `cached_value_json[Bridge].ranking` | Thread ranking passed to Bridge and checked by Shield. |
| `cached_value_json[Bridge].ranking.definition_id` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.scope_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.group` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.member_ids` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.start` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.end_exclusive` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].ranking.order` | Copied from Thread.ranking; checked against permitted data by Shield. |
| `cached_value_json[Bridge].unit` | Library's approved company measure definition used by Bridge. |
| `cached_value_json[Bridge].data_version` | Bridge reads company data version and identifies the operational source file. |
| `cached_value_json[Bridge].source` | Bridge reads company data version and identifies the operational source file. |
| `cached_value_json[Bridge].totals` | Bridge ranks the selected groups; Shield independently checks the member set, figures and order. |
| `cached_value_json[Bridge].totals[].asset_id` | Bridge: member identifier and IDs of contributing client source rows. |
| `cached_value_json[Bridge].totals[].record_ids` | Bridge: member identifier and IDs of contributing client source rows. |
| `cached_value_json[Bridge].totals[].value` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `cached_value_json[Bridge].totals[].rank` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |
| `cached_value_json[Bridge].totals[].reason` | Bridge: approved measure over source rows, its rank including ties, or reason for no value; Shield verifies. |

