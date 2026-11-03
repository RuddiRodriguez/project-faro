"""Faro-owned table columns and their origins. IDs are scoped to the verified company."""
COLUMNS = {
    "conversations": [
        ("conversation_id","TEXT","Compass generates a UUID on the first message; later requests return that same ID."),
        ("company_id","TEXT","Gate: company on the signed-in demo account."),
        ("user_id","TEXT","Gate: verified account that started the conversation."),
        ("original_question","TEXT","First user message in supplied history, otherwise the first request.question."),
        ("created_at","TIMESTAMP","Compass UTC clock when the conversation starts."),
        ("access_json","JSON","Gate result at creation: user_id, company_id, permitted_scope_ids and permission_version from users.json."),
        ("initial_history_json","JSON","Only role and content supplied by the caller when starting a conversation; not independently verified history.")],
    "model_calls": [
        ("turn_id","TEXT","Compass turn ID, passed to the service with the request."),
        ("call_id","TEXT","Shared utils generates one ID per logical model call; retries keep it."),
        ("service","TEXT","Name of the service making the model call."),
        ("started_ns","INTEGER","Service clock at the start of the logical call, Unix nanoseconds."),
        ("explanations_json","JSON","Model response: brief initial_analysis and reasoning per attempt, with its attempt number. Not private chain of thought."),
        ("outcomes_json","JSON","One outcome per provider attempt, in order; in_progress until the provider returns.")],
    "turns": [
        ("turn_id","TEXT","Compass UUID for this individual message."),
        ("conversation_id","TEXT","Foreign key to the owned conversation selected by Compass after Gate checks access."),
        ("turn_number","INTEGER","Compass: previous saved turn count plus one, under the conversation lock."),
        ("message","TEXT","Exact current user message from request.question."),
        ("created_at","TIMESTAMP","Compass UTC clock before processing this turn."),
        ("status","TEXT","Compass: started or failed; otherwise Shield's status or the final next-action decision."),
        ("decision_source","TEXT","Compass identifies Signal or Bridge as the producer of the final action."),
        ("plan_json","JSON","Bridge's proposed source read, when available; null for a clarification before reading."),
        ("response_json","JSON","Service outputs collected by Compass; individual fields are listed in the field guide."),
        ("cache_events_json","JSON","Compass lookup events for this turn: service, collection, key, fresh/cache/rejected and producing turn."),
        ("model_attempts_tracked","INTEGER","Compass: tracking enabled for this turn. Older turns have no counts."),
        ("error","TEXT","Service, endpoint and failure type when a service call fails; otherwise the exception class. No invented substitute response."),
        ("elapsed_ms","INTEGER","Compass monotonic timer: milliseconds from turn processing start to outcome. Not an invoice."),
        ("cache_version","TEXT","Compass fingerprint of the deployed cache policy, service code and settings.")],
    "field_origins": [
        ("table_name","TEXT","Declared Faro table whose field is described."),
        ("field_path","TEXT","Column name, or nested path in its saved JSON value; [] denotes an item."),
        ("source","TEXT","Description defined in the Faro schema or recorded service output contract.")]}
CACHE = [
    ("cache_key","TEXT","Compass hash of company, permissions, company information, policy version, service and exact inputs; AI keys also include the user."),
    ("company_id","TEXT","Gate: the company permitted to reuse this entry."),
    ("service","TEXT","Compass identifies the producing service call."),
    ("version","TEXT","Compass cache policy fingerprint when the entry was written."),
    ("cached_value_json","JSON","Typed output of the named AI service, or Bridge facts independently verified by Shield."),
    ("expires_at","TIMESTAMP","Compass UTC save time plus 120 days."),
    ("produced_by_turn","TEXT","Foreign key to the turn that actually produced this value; absent if an older record did not save it.")]
COLUMNS["ai_cache"] = CACHE
COLUMNS["data_cache"] = CACHE


def field_origins():
    for table, columns in COLUMNS.items():
        for field, _, origin in columns:
            yield table, field, origin
    for path, source in NESTED.items():
        yield "turns", path, source
    for field in ("user_id","company_id","permitted_scope_ids","permission_version"):
        yield "conversations","access_json."+field,"Gate reads this field from the saved account in users.json."
    for field in ("role","content"):
        yield "conversations","initial_history_json[]."+field,"Caller-supplied history or the previous verified question, after Gate access and ownership checks."
    for service, branch in (("Signal","decision"),
                            ("Guide","followup"),("Voice","answer"),("Bridge","evidence")):
        table = "data_cache" if service=="Bridge" else "ai_cache"
        prefix = "plan_json" if branch is None else "response_json."+branch
        for path, source in NESTED.items():
            if path.startswith(prefix+"."):
                suffix=path[len(prefix):]
                yield table, f"cached_value_json[{service}]"+suffix, source if service!="Signal" else "Signal's classification before Bridge reads the data."


NESTED = {}
def fields(prefix, names, origin):
    for name in names.split():
        NESTED[prefix+"."+name]=origin


fields("cache_events_json[]","collection service","Compass: selected cache table and service call.")
fields("cache_events_json[]","key","Compass cache lookup fingerprint; joins to cache_key in the named table.")
fields("cache_events_json[]","result_source","Compass: fresh call, valid cache hit, or data rejected by Shield.")
fields("cache_events_json[]","produced_by_turn","Saved entry's originating turn; for a new entry, the current turn ID.")
fields("response_json","question","User: exact current message.")
fields("response_json","conversation_id turn_id","Compass: same IDs as this row and its parent.")
fields("response_json","rewrite search decision followup evidence verification answer","Compass stores only the services reached on this route; see child fields.")
fields("response_json.rewrite","question unclear_references","Thread: wording, unresolved references, reason for this turn, and retained details of the request.")
fields("response_json.rewrite","used_ai model_name","Thread: whether the original rewrite used AI and which model answered.")
fields("response_json.rewrite","token_usage","Provider usage for the original prediction, not a new charge on a cache hit.")
fields("response_json.rewrite.token_usage","prompt_tokens completion_tokens prompt_tokens_details completion_tokens_details","OpenAI usage returned to Thread through utils; absent when not reported.")
fields("response_json.rewrite.token_usage.prompt_tokens_details","audio_tokens cached_tokens cache_write_tokens","OpenAI prompt-token breakdown on the original model call.")
fields("response_json.rewrite.token_usage.completion_tokens_details","accepted_prediction_tokens audio_tokens reasoning_tokens rejected_prediction_tokens","OpenAI completion-token breakdown on the original model call.")
fields("response_json.search","query matches","Scout: search input from Thread and permitted matches from its company index.")
fields("response_json.search.matches[]","document_id title text source version","Scout: passage from a permitted connected source, with its location and version.")
fields("response_json.search.matches[]","source_id page start end","Scout: connected source ID, PDF page and exact character positions in extracted page text; non-PDF passages describe fields.")
fields("response_json.search.matches[]","file_reference score","Scout: index source reference and relevance score, not proof of correctness.")
fields("response_json.decision","action missing_choice","Signal's classification or Bridge's clarification/stop; see decision_source.")
fields("response_json.followup","followup_text initial_analysis reasoning","Guide: clarification generated for the missing choice.")
read_fields="source scope_ids member_ids group start end_exclusive expression"
fields("plan_json",read_fields,"Bridge model proposes the permitted source and bounded read through utils.")
fields("response_json.verification","status reason facts","Shield checks source records and whether the read answers the question.")
for prefix in ("response_json.evidence","response_json.verification.facts"):
    fields(prefix,"question company_id","Compass supplies the question and Gate company.")
    fields(prefix,"status reason read","Bridge returns read status, explanation and selected read.")
    fields(prefix+".read",read_fields,"Bridge model produces the read, checked against permitted sources.")
    fields(prefix,"data_version source unit period","Bridge reads the version, source, unit and dates from company records.")
    fields(prefix,"supporting","Additional replayable reads from the same answer, in evidence ID order.")
    fields(prefix,"link_check","Bridge: successful native join checks, replayed by Shield; row counts, unique right keys, no missing keys and complete key matches.")
    fields(prefix,"catalogue_version","Fingerprint of the company catalogue visible for this request.")
    fields(prefix,"findings","Bridge proposes findings; Shield returns only the supported ones.")
    fields(prefix+".findings[]","text evidence_ids","Reviewed finding and citations: 0 for catalogue, positive IDs for reads.")
    fields(prefix,"record_ids rows","Identifiers of the contributing source records and the pandas result.")
    fields(prefix+".rows[]","member scope_name asset_type activity_date value","Checked pandas result; member is present only for grouped output.")
fields("response_json.answer","status","Operational answers use Shield's decision. Unsupported data requests may be withheld without a ranking.")
fields("response_json.answer","text mode","Voice displays Shield-reviewed findings, a direct limitation, or checked legacy wording.")
fields("response_json.answer","sources definition","Voice copies Bridge's operational source and Scout's matched source passage and reference.")

for service in ("rewrite", "decision"):
    fields("response_json."+service,"initial_analysis reasoning","Service model response: brief factual assessment and decision justification.")
