"""Faro-owned tables: Parquet rows in the demo, independent of client data sources."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from fcntl import flock, LOCK_EX, LOCK_UN
from hashlib import sha256
import json
import os
import pandas as pd
import pyarrow as pa
from utils.llms.model_attempts import read_attempts, read_explanations
from compass.collection_schema import COLUMNS, field_origins
from pathlib import Path
from uuid import uuid4

from pydantic_core import to_jsonable_python
from utils.llms.common.intelligence_level import IntelligenceLevel


def now():
    return datetime.now(timezone.utc)


def digest(value):
    payload = json.dumps(to_jsonable_python(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode()).hexdigest()


def cache_version():
    # Fingerprint the installed demo service policies. For separately deployed APIs,
    # change FARO_CACHE_VERSION when their model, settings or code changes.
    demo = Path(__file__).resolve().parents[5]
    version = sha256()
    for service in ("thread", "signal", "guide", "bridge", "shield", "voice"):
        for path in sorted((demo / service).glob("*/infer/**/*.py")):
            version.update(path.relative_to(demo).as_posix().encode())
            version.update(path.read_bytes())
    return digest(["parquet-v1", os.getenv("FARO_CACHE_VERSION", "1"), IntelligenceLevel.YOLO.settings, version.hexdigest()])


class ConversationInputError(ValueError):
    pass


class DataCollection:
    def __init__(self, root):
        self.root = Path(root)
        self.version = cache_version()

    def path(self, company, table, key):
        return self.root / company / table / (str(key)+".parquet")

    def write(self, path, table, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        types = {"TEXT":pa.string(), "JSON":pa.string(), "TIMESTAMP":pa.timestamp("us",tz="UTC"), "INTEGER":pa.int64()}
        schema = pa.schema([(name,types[kind]) for name,kind,_ in COLUMNS[table]])
        frame = pd.DataFrame(rows, columns=schema.names)
        for name,kind,_ in COLUMNS[table]:
            if kind == "TIMESTAMP":
                frame[name] = pd.to_datetime(frame[name], utc=True)
        temp = path.with_suffix(f".{uuid4().hex}.tmp")
        frame.to_parquet(temp, engine="pyarrow", schema=schema, index=False)
        temp.replace(path)

    def ensure_guide(self, company):
        path = self.path(company, "field_origins", "fields")
        if not path.exists() or path.stat().st_mtime < Path(__file__).with_name("collection_schema.py").stat().st_mtime:
            self.write(path, "field_origins", [dict(table_name=t, field_path=p, source=s) for t,p,s in field_origins()])

    def read_conversation(self, company, cid):
        path = self.path(company, "conversations", cid)
        if not path.exists():
            return None
        row = pd.read_parquet(path).to_dict("records")[0]
        history = json.loads(row["initial_history_json"])
        doc = dict(_id=str(cid), company_id=company, user_id=row["user_id"], original_question=row["original_question"],
                   created_at=row["created_at"].isoformat(),access=json.loads(row["access_json"]),
                   initial_history=history,supplied_history=bool(history),messages=list(history),turns=[])
        folder = self.root / company / "turns" / str(cid)
        for path in sorted(folder.glob("*.parquet")):
            frame = pd.read_parquet(path)
            row = frame.astype(object).where(frame.notna(), None).to_dict("records")[0]
            t = dict(_id=row["turn_id"], number=row["turn_number"],message=row["message"],language=row["language"],
                     status=row["status"],created_at=row["created_at"].isoformat(),cache=json.loads(row["cache_events_json"]),
                     plan=json.loads(row["plan_json"]),response=json.loads(row["response_json"]),
                     elapsed_ms=row["elapsed_ms"],error=row["error"],decision_source=row["decision_source"])
            t["model_attempts"] = read_attempts(self.root, company, t["_id"]) if row.get("model_attempts_tracked") else None
            t["model_explanations"] = read_explanations(self.root, company, t["_id"]) if row.get("model_attempts_tracked") else None
            doc["turns"].append(t)
            doc["messages"].append(dict(role="user",content=t["message"]))
            response = t["response"] or {}
            reply = (response.get("followup") or {}).get("followup_text") or (response.get("answer") or {}).get("text")
            if reply:
                doc["messages"].append(dict(role="assistant",content=reply))
        return doc

    @contextmanager
    def conversation(self, request, access):
        cid = request.conversation_id or uuid4()
        folder = self.root / access.company_id / "locks"
        folder.mkdir(parents=True, exist_ok=True)
        # Serialize turns in this conversation, not model calls from other users.
        with (folder / f"{cid}.lock").open("a") as lock:
            flock(lock, LOCK_EX)
            try:
                if request.conversation_id:
                    doc = self.read_conversation(access.company_id, cid)
                    if doc is None or doc["access"] != access.model_dump(mode="json"):
                        raise PermissionError("Conversation unavailable under current permissions")
                    if request.conversation:
                        raise ConversationInputError("Send only the new message when continuing a saved conversation")
                else:
                    history = [m.model_dump() for m in request.conversation]
                    original = next((m["content"] for m in history if m["role"] == "user"), request.question)
                    if request.previous_answer_id:
                        previous = self.read_conversation(access.company_id, request.previous_answer_id)
                        if not previous or previous["access"] != access.model_dump(mode="json"):
                            raise PermissionError("Previous answer is not available to this user.")
                        turn = previous["turns"][-1]
                        if turn["status"] != "verified":
                            raise ConversationInputError("Only a verified question can supply follow-up context.")
                        history = [dict(role="user", content=turn["response"]["rewrite"]["question"])]
                    doc = dict(_id=str(cid), company_id=access.company_id, user_id=access.user_id,
                               original_question=original, access=access.model_dump(mode="json"),
                               created_at=now().isoformat(), initial_history=history, supplied_history=bool(history), messages=list(history), turns=[])
                yield doc
            finally:
                flock(lock, LOCK_UN)

    def save_conversation(self, doc):
        company, cid = doc["company_id"], doc["_id"]
        self.ensure_guide(company)
        header = self.path(company, "conversations", cid)
        if not header.exists():
            self.write(header,"conversations",[dict(conversation_id=cid, company_id=company, user_id=doc["user_id"],
                original_question=doc["original_question"],created_at=doc["created_at"],access_json=json.dumps(doc["access"]),
                initial_history_json=json.dumps(doc["initial_history"],ensure_ascii=False))])
        t = doc["turns"][-1]
        row = dict(turn_id=t["_id"],conversation_id=cid,turn_number=t["number"],message=t["message"],
            language=t["language"],created_at=t["created_at"],status=t["status"],decision_source=t.get("decision_source"),
            plan_json=json.dumps(t.get("plan")),response_json=json.dumps(t.get("response"),ensure_ascii=False),
            model_attempts_tracked=int(t.get("model_attempts_tracked",False)), cache_events_json=json.dumps(t["cache"]),error=t.get("error"),elapsed_ms=t.get("elapsed_ms"),
            cache_version=t.get("cache_version",self.version))
        self.write(self.path(company, "turns", f"{cid}/{t['number']:08d}"),"turns",[row])

    def fetch(self, company, kind, key, model):
        path = self.path(company, kind+"_cache", key)
        if path.exists():
            row = pd.read_parquet(path).to_dict("records")[0]
            if row["version"] == self.version and row["expires_at"] > now():
                return model.model_validate_json(row["cached_value_json"]), row["produced_by_turn"]
        return None,None

    def save_to_cache(self, company, kind, key, service, result, turn_id):
        table = kind+"_cache"
        self.write(self.path(company, table, key),table,[dict(cache_key=key,company_id=company,
            service=service,version=self.version,cached_value_json=result.model_dump_json(by_alias=True),
            expires_at=now()+timedelta(days=120),produced_by_turn=turn_id)])

    def discard(self, company, kind, key):
        self.path(company, kind+"_cache",key).unlink(missing_ok=True)


class TurnCache:
    def __init__(self, store, access, information, events, turn_id, opening=True):
        self.opening = opening
        self.store = store
        self.company = access.company_id
        self.user = access.user_id
        self.context = digest([sorted(access.permitted_scope_ids), access.permission_version, information])
        self.events = events
        self.turn_id = turn_id

    def lookup(self, kind, service, inputs, model):
        if not self.opening:
            return None, None
        key = digest([self.company, self.user if kind == "ai" else None, self.context,
                      self.store.version, service, inputs])
        result, origin = self.store.fetch(self.company, kind, key, model)
        self.events.append(dict(collection=kind+"_cache", service=service, key=key,
                                produced_by_turn=origin, result_source="cache" if result is not None else "fresh"))
        return key, result

    def ai(self, service, inputs, model, predict, eligible=lambda result: True):
        key, result = self.lookup("ai", service, inputs, model)
        if result is None:
            result = predict()
            if self.opening and eligible(result):
                self.store.save_to_cache(self.company, "ai", key, service, result, self.turn_id)
                self.events[-1]["produced_by_turn"] = self.turn_id
        return result
