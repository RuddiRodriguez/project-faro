-- Faro-owned SQL design. Client data may come from any source.

CREATE TABLE conversations (
  conversation_id TEXT PRIMARY KEY,
  company_id TEXT,
  user_id TEXT,
  original_question TEXT,
  created_at TIMESTAMP,
  access_json JSON,
  initial_history_json JSON
);

CREATE TABLE turns (
  turn_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
  turn_number INTEGER,
  message TEXT,
  created_at TIMESTAMP,
  status TEXT,
  decision_source TEXT,
  plan_json JSON,
  response_json JSON,
  cache_events_json JSON,
  model_attempts_tracked INTEGER,
  error TEXT,
  elapsed_ms INTEGER,
  cache_version TEXT,
  UNIQUE (conversation_id, turn_number)
);

CREATE TABLE model_calls (
  turn_id TEXT NOT NULL REFERENCES turns(turn_id),
  call_id TEXT PRIMARY KEY,
  service TEXT,
  started_ns INTEGER,
  explanations_json JSON,
  outcomes_json JSON
);

CREATE TABLE field_origins (
  table_name TEXT,
  field_path TEXT,
  source TEXT,
  PRIMARY KEY (table_name, field_path)
);

CREATE TABLE ai_cache (
  cache_key TEXT PRIMARY KEY,
  company_id TEXT,
  service TEXT,
  version TEXT,
  cached_value_json JSON,
  expires_at TIMESTAMP,
  produced_by_turn TEXT REFERENCES turns(turn_id)
);

CREATE TABLE data_cache (
  cache_key TEXT PRIMARY KEY,
  company_id TEXT,
  service TEXT,
  version TEXT,
  cached_value_json JSON,
  expires_at TIMESTAMP,
  produced_by_turn TEXT REFERENCES turns(turn_id)
);
