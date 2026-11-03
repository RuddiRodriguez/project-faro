"""Record provider attempts independently of the service response reaching Compass."""
from contextvars import ContextVar
from functools import wraps
import json
import os
from pathlib import Path
from time import time_ns
from uuid import UUID, uuid4

import openai
import pyarrow as pa
import pyarrow.parquet as pq

from ..openai_client.exceptions import OpenAiRecoverableError

turn_context = ContextVar("faro_turn", default=None)
current_call = ContextVar("faro_model_call", default=None)
DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "local_data/data_collection"


def install_attempt_tracking(app, service):
    @app.middleware("http")
    async def model_context(request, call_next):
        company = request.headers.get("x-faro-company")
        turn = request.headers.get("x-faro-turn")
        if not (turn and company and company.replace("-", "_").isidentifier()):
            return await call_next(request)
        token = turn_context.set((company, str(UUID(turn)), service))
        try:
            return await call_next(request)
        finally:
            turn_context.reset(token)


def track_call(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        if not turn_context.get():
            return fn(*args, **kwargs)
        token = current_call.set((str(uuid4()), time_ns(), []))
        try:
            return fn(*args, **kwargs)
        finally:
            current_call.reset(token)
    return run


def track_attempt(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        if not current_call.get():
            return fn(*args, **kwargs)
        company, turn, service = turn_context.get()
        call_id, started, outcomes = current_call.get()
        folder = Path(os.getenv("FARO_COLLECTION_PATH", DEFAULT_ROOT)) / company / "model_calls" / turn
        folder.mkdir(parents=True, exist_ok=True)
        explanations = []
        def save():
            row = dict(turn_id=turn, call_id=call_id, service=service, started_ns=started, outcomes_json=json.dumps(outcomes), explanations_json=json.dumps(explanations))
            temp = folder / (call_id + ".tmp")
            pq.write_table(pa.Table.from_pylist([row]), temp)
            temp.replace(folder / (call_id + ".parquet"))
        outcomes.append("in_progress")
        save()
        try:
            result = fn(*args, **kwargs)
        except OpenAiRecoverableError as error:
            cause = error.cause_exception
            outcomes[-1] = "timeout" if isinstance(cause, openai.APITimeoutError) else type(cause or error).__name__
            raise
        except Exception as error:
            outcomes[-1] = type(getattr(error, "cause_exception", None) or error).__name__
            raise
        else:
            outcomes[-1] = "success" if result.is_success else "invalid_response"
            values = {}
            for tool in result.assistant_tools or []:
                parsed = getattr(tool, "parsed_arguments", None)
                if isinstance(parsed, dict):
                    values.update({k:parsed[k] for k in ("initial_analysis","reasoning") if k in parsed})
            if result.decisions_response:
                for answer in result.decisions_response.get("answers", []):
                    if answer.get("name") in ("initial_analysis","reasoning"):
                        values[answer["name"]] = answer.get("choice")
            if values:
                explanations.append(dict(attempt=len(outcomes), **values))
            return result
        finally:
            save()
    return run


def read_attempts(root, company, turn):
    folder = Path(root) / company / "model_calls" / str(turn)
    rows = [pq.read_table(path).to_pylist()[0] for path in folder.glob("*.parquet")]
    services = {}
    for row in sorted(rows, key=lambda item: item["started_ns"]):
        service = services.setdefault(row["service"], {"attempts":0, "calls":[]})
        outcomes = json.loads(row["outcomes_json"])
        service["attempts"] += len(outcomes)
        service["calls"].append(outcomes)
    return services


def read_explanations(root, company, turn):
    folder = Path(root) / company / "model_calls" / str(turn)
    rows = [pq.read_table(path).to_pylist()[0] for path in folder.glob("*.parquet")]
    return [dict(service=row["service"], call_id=row["call_id"],
                 explanations=json.loads(row.get("explanations_json") or "[]"))
            for row in sorted(rows, key=lambda item:item["started_ns"])]
