"""Load permitted JSON records; run the model's expression on an in-memory dataframe."""
import json
import os
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from utils.connector_client import sources as connected_sources
from bridge.connected import execute_connected
from bridge.predictor_output import PredictorOutput
from bridge.records import read_records


def load(path, name):
    return json.loads((path / f"{name}.json").read_text())


def snapshot_id(catalogue):
    return sha256(json.dumps(catalogue, sort_keys=True).encode()).hexdigest()


def catalogue(path, request):
    company = next(c for c in load(path, "companies") if c["company_id"] == request.company_id)
    scopes = {s["scope_id"]: s["name"] for s in load(path, "scopes") if s["company_id"] == request.company_id
              and s["scope_id"] in request.permitted_scope_ids}
    approved = [d for d in load(path, "documents") if d["company_id"] == request.company_id
                and d["status"] == "approved" and d["document_id"] in request.definition_ids
                and set(scopes).intersection(d["scope_ids"])]
    docs = {d["document_id"]: dict(meaning=d["text"], measure=d["measure"]) for d in approved if d.get("measure")}
    def permitted(name):
        return [r for r in load(path,name) if r["company_id"] == request.company_id and r["scope_id"] in scopes]
    operational = permitted("activity")
    metadata = {"company_id","scope_id","asset_id","activity_date","_id","record_id","revision","deleted"}
    fields = sorted({k for row in operational for k,v in row.items() if k not in metadata and isinstance(v,(int,float,str,bool))})
    agreements = permitted("agreements") if (path/"agreements.json").exists() else []
    assets = [a for a in load(path, "assets") if a["company_id"] == request.company_id and a["scope_id"] in scopes]
    now = datetime.fromisoformat(load(path, "manifest")["default_now_utc"]).astimezone(ZoneInfo(company["timezone"]))
    connected={item.id:item.model_dump() for item in connected_sources(request.company_id,list(scopes)).items}
    return dict(connected=connected,reference_date=now.date().isoformat(), scopes=scopes, data_version=company["data_version"],
                groups={kind: [a["asset_id"] for a in assets if a["asset_type"] == kind] for kind in sorted({a["asset_type"] for a in assets})},
                dimensions=["asset_id", "scope_id", "scope_name", "asset_type"],
                definitions=[{**{k:d[k] for k in ("document_id","title","text","version","source","valid_from","valid_until_exclusive") if k in d},
                              "scopes":sorted(set(scopes).intersection(d["scope_ids"]))} for d in approved],
                agreements=[r for r in agreements if r["status"]=="approved"],
                history={s: sorted({(r["period_start"],r["period_end_exclusive"],r["status"]) for r in permitted("coverage")
                                  if r["scope_id"]==s and r["data_version"]==company["data_version"]}) for s in scopes},
                sources={"register":{"description":"Active inventory; one row per member at the snapshot date.",
                                     "fields":sorted({"scope_name", *(k for a in assets for k in a
                                                      if k not in {"company_id","_id"})})},
                         **({"activity":{"fields":fields,"description":"Checked daily activity; interpret fields using applicable approved definitions."}} if operational else {}),
                         **docs})


def run_read(expression, records, columns):
    worker = Path(__file__).with_name("worker.py")
    if sys.platform != "darwin":
        raise ValueError("No isolated pandas runner configured on this platform.")
    command = [sys.executable, "-I", str(worker)]
    try:
        proc = subprocess.run(command, input=json.dumps(dict(expression=expression, records=records, columns=columns)),
            text=True, capture_output=True, timeout=12, env={"OPENBLAS_NUM_THREADS":"1", "OMP_NUM_THREADS":"1"})
    except subprocess.TimeoutExpired as error:
        raise ValueError("The dataframe read timed out.") from error
    if proc.returncode:
        raise ValueError(proc.stderr.strip() or "The dataframe read stopped.")
    return json.loads(proc.stdout)


def execute(path, request, read):
    cat = catalogue(path, request)
    scopes = read.scope_ids or list(cat["scopes"])
    members = cat["groups"].get(read.group, [])
    if read.source in cat["connected"]:
        return execute_connected(request,read,cat,run_read)
    if read.link is not None:
        raise ValueError("Link requires two connected items.")
    if not scopes or not set(scopes).issubset(cat["scopes"]) or not set(read.member_ids).issubset(members):
        raise PermissionError("Selection is outside the permitted records.")
    if read.group not in cat["groups"] or read.source not in cat["sources"]:
        raise ValueError("No approved source for the requested group or measure.")
    read_scoped = read.model_copy(update={"scope_ids":scopes})
    assets = [a for a in load(path, "assets") if a["company_id"] == request.company_id and a["scope_id"] in scopes
              and a["asset_type"] == read.group and (not read.member_ids or a["asset_id"] in read.member_ids)]
    if not set(read.member_ids).issubset({a["asset_id"] for a in assets}):
        raise ValueError("A selected member is outside the requested locations.")
    if read.source == "register":
        if read.end_exclusive:
            raise ValueError("The register supports a snapshot, not a period.")
        as_of = read.start or date.fromisoformat(cat["reference_date"])
        if as_of > date.fromisoformat(cat["reference_date"]):
            raise ValueError("No register snapshot for this future date.")
        ids = sorted(a["asset_id"] for a in assets if a["active_from"] <= as_of.isoformat()
                     and (not a["active_until_exclusive"] or as_of.isoformat() < a["active_until_exclusive"]))
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate register entries.")
        data = [a for a in assets if a["asset_id"] in ids]
        fields = cat["sources"]["register"]["fields"]
        period, source, unit, measure = f"as of {as_of}", "assets.json", "members", {}
    else:
        start, end = read.start, read.end_exclusive
        if (start is None) != (end is None):
            raise ValueError("The read has only one date bound.")
        if start is None:
            keys = {a["asset_id"] for a in assets}
            # Include the coverage declarations too: a missing first/last day must not silently shrink history.
            reports = [r for r in load(path, "coverage") if r["company_id"] == request.company_id
                       and r["scope_id"] in scopes and r["asset_id"] in keys and r["data_version"] == cat["data_version"]]
            dates = [date.fromisoformat(r["activity_date"]) for r in load(path, "activity") if
                     r["company_id"] == request.company_id and r["scope_id"] in scopes and r["asset_id"] in keys]
            if not reports or not dates:
                raise ValueError("No confirmed available history.")
            start = min(min(dates), min(date.fromisoformat(r["period_start"]) for r in reports))
            end = max(max(dates) + timedelta(days=1), max(date.fromisoformat(r["period_end_exclusive"]) for r in reports))
        _, measure, groups = read_records(path, request, read_scoped.model_copy(update={"start":start,"end_exclusive":end}))
        date_sets = {tuple(r["activity_date"] for r in rows) for rows in groups.values()}
        if len(date_sets) > 1 and ".groupby(" in read.expression.replace(" ", ""):
            raise ValueError("Members do not have equal coverage for comparison.")
        ids = sorted(r["record_id"] for rows in groups.values() for r in rows)
        if measure is None:
            fields = [*cat["dimensions"], "activity_date", *cat["sources"]["activity"]["fields"]]
        else:
            fields = [*cat["dimensions"], "activity_date", measure["numerator"]]
            if measure["denominator"]:
                fields.append(measure["denominator"])
        data = [dict(r, asset_type=read.group) for rows in groups.values() for r in rows]
        period, source, unit = f"{start} through {end-timedelta(days=1)}", "activity.json", measure["unit"] if measure else None
    records = [{field: cat["scopes"][row["scope_id"]] if field == "scope_name" else row.get(field)
                for field in fields} for row in data]
    if read.source == "activity" and any(row.get(field) is None for row in records for field in cat["sources"]["activity"]["fields"]):
        raise ValueError("Missing operational field in the selected records; the full data read cannot be verified.")
    rows = run_read(read.expression, records, fields)
    if not rows:
        raise ValueError("No verified value for the requested read.")
    for row in rows:
        if "asset_id" in row:
            row["member"] = row.pop("asset_id")
        if isinstance(row.get("scope_id"), str) and row["scope_id"] in cat["scopes"]:
            row["scope_name"] = cat["scopes"][row.pop("scope_id")]
    content=json.dumps(dict(source=source,record_ids=ids,records=records),ensure_ascii=False,indent=2).encode()
    version=sha256(content).hexdigest()
    folder=Path(os.getenv("FARO_DOCUMENT_PATH", Path(__file__).resolve().parents[5]/"local_data/source_documents"))
    saved=folder/request.company_id/version/(Path(source).stem+"-permitted-records.json")
    saved.parent.mkdir(parents=True,exist_ok=True)
    saved.write_bytes(content)
    document=dict(name=saved.name,uri=saved.resolve().as_uri(),version=version)
    return PredictorOutput(status="ready", company_id=request.company_id, question=request.question,
        read=read, source=source, unit=unit, period=period, data_version=cat["data_version"],
        rows=rows, record_ids=ids, source_evidence=[dict(source=source,version=cat["data_version"],
            references=[f"{source}#{key}" for key in ids],document=document)])
