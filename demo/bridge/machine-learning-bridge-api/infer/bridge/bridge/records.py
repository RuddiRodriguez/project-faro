"""Read the prepared company records for one approved request."""
import json
import math
from datetime import date, timedelta
from pathlib import Path


def read_records(path: Path, request, plan):
    def read(name):
        return json.loads((path / f"{name}.json").read_text())

    scopes = set(plan.scope_ids)
    if not scopes or not scopes.issubset(request.permitted_scope_ids):
        raise PermissionError("Requested scope is not permitted.")
    company = next(c for c in read("companies") if c["company_id"] == request.company_id)
    start, end = plan.start.isoformat(), plan.end_exclusive.isoformat()
    if start >= end:
        raise ValueError("Invalid reporting period.")
    docs = [d for d in read("documents") if d["company_id"] == request.company_id and d["status"] == "approved"
            and d["document_id"] == plan.source and d["document_id"] in request.definition_ids
            and scopes.issubset(d["scope_ids"]) and d.get("valid_from") and d["valid_from"] <= start
            and (not d.get("valid_until_exclusive") or end <= d["valid_until_exclusive"])
            and d.get("measure") and d["version"] == d["measure"]["version"]]
    if plan.source != "activity" and (len(docs) != 1 or docs[0]["measure"]["group"] != plan.group):
        raise ValueError("No approved measure for this group and period.")
    measure = docs[0]["measure"] if docs else None

    def scoped(name):
        return [r for r in read(name) if r["company_id"] == request.company_id and r["scope_id"] in scopes]

    members = [a for a in scoped("assets") if a["asset_type"] == plan.group and a["active_from"] < end
               and (not a["active_until_exclusive"] or a["active_until_exclusive"] > start)
               and (not plan.member_ids or a["asset_id"] in plan.member_ids)]
    if not members or (plan.member_ids and set(plan.member_ids) != {a["asset_id"] for a in members}):
        raise ValueError("Requested members not found in the permitted records.")
    revisions = {}
    for row in scoped("activity"):
        if start <= row["activity_date"] < end:
            versions = revisions.setdefault(row["record_id"], {})
            if versions.setdefault(row["revision"], row) != row:
                raise ValueError("Conflicting record revisions.")
    latest = [versions[max(versions)] for versions in revisions.values()]
    coverage = scoped("coverage")
    groups = {}
    incomplete = []
    unconfirmed = []
    for member in members:
        key, scope = member["asset_id"], member["scope_id"]
        if key in groups:
            raise ValueError("Member identifiers must be unique within the requested scopes.")
        first = max(plan.start, date.fromisoformat(member["active_from"]))
        until = min(plan.end_exclusive, date.fromisoformat(member["active_until_exclusive"])) if member["active_until_exclusive"] else plan.end_exclusive
        days = [(first + timedelta(days=i)).isoformat() for i in range((until-first).days)]
        rows = sorted((r for r in latest if r["asset_id"] == key and r["scope_id"] == scope and not r["deleted"]),
                      key=lambda r:r["activity_date"])
        reports = [r for r in coverage if r["asset_id"] == key and r["scope_id"] == scope
                   and r["period_start"] < end and start < r["period_end_exclusive"]
                   and r["data_version"] == company["data_version"]]
        if [r["activity_date"] for r in rows] != days:
            incomplete.append(f"{key} ({len(set(r['activity_date'] for r in rows))}/{len(days)} days recorded)")
            continue
        def confirmed(report):
            lo = max(date.fromisoformat(report["period_start"]), date.fromisoformat(member["active_from"]))
            hi = date.fromisoformat(report["period_end_exclusive"])
            if member["active_until_exclusive"]:
                hi = min(hi, date.fromisoformat(member["active_until_exclusive"]))
            return report["status"] == "complete" and report["expected_days"] == report["received_days"] == (hi - lo).days

        if not all(confirmed(r) for r in reports) or not all(
                sum(r["period_start"] <= day < r["period_end_exclusive"] for r in reports) == 1 for day in days):
            unconfirmed.append(key)
            continue
        for field in filter(None, (measure["numerator"], measure["denominator"])) if measure else ():
            if any(type(r.get(field)) not in (float,int) or not math.isfinite(r[field])
                   or (measure.get("minimum_input") is not None and r[field] < measure["minimum_input"]) for r in rows):
                raise ValueError(f"Missing or invalid {field} for {key}.")
        groups[key] = rows
    if incomplete or unconfirmed:
        details = []
        if incomplete:
            details.append("Incomplete daily records for " + ", ".join(incomplete) + ".")
        if unconfirmed:
            details.append("All daily records present but no complete confirmation for these exact dates: "
                           + ", ".join(unconfirmed) + ".")
        last_day = plan.end_exclusive - timedelta(days=1)
        raise ValueError(f"From {start} through {last_day}, " + " ".join(details) + " Cannot verify the full result.")
    return company["data_version"], measure, groups
