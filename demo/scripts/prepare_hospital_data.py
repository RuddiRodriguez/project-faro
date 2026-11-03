"""Expand fictional Cedar data only. Rerunning replaces Cedar's generated records."""
import json
from calendar import monthrange
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "local_data/demo_dataset"
HOSPITALS = [
    ("riverside", "Riverside Hospital", "Rotterdam", 140, 30, 75),
    ("hillview", "Hillview Hospital", "Utrecht", 100, 45, 85),
    ("lakeside", "Lakeside Hospital", "Amsterdam", 220, 25, 90),
    ("westhaven", "Westhaven Hospital", "The Hague", 180, 38, 80),
    ("meadow", "Meadow Hospital", "Eindhoven", 80, 20, 65),
    ("central", "Central Hospital", "Groningen", 160, 50, 95),
]


def prepare():
    def read(name):
        return json.loads((ROOT / f"{name}.json").read_text())

    def save(name, value):
        (ROOT / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n")

    scopes = [h[0] for h in HOSPITALS]
    tables = {name: [r for r in read(name) if r.get("company_id") != "cedar"]
              for name in ("assets", "scopes", "activity", "coverage", "documents")}
    companies = read("companies")
    company = next(c for c in companies if c["company_id"] == "cedar")
    company.update(data_version="cedar-v2", definition_version="v2", task_document_ids=["cedar_tasks"])
    save("companies", companies)
    users = read("users")
    for user in users:
        if user["company_id"] == "cedar":
            user["permission_version"] = "v2"
            if user["user_id"] == "hospital_ops":
                user["scope_ids"] = scopes
    save("users", users)
    for i, (scope, name, city, beds, waiting, occupancy) in enumerate(HOSPITALS):
        tables["scopes"].append(dict(_id=scope, company_id="cedar", scope_id=scope, name=name, aliases=[city]))
        tables["assets"].append(dict(_id=name, company_id="cedar", scope_id=scope, asset_id=name,
            asset_type="hospital", city=city, staffed_beds=beds, active_from="2026-07-01", active_until_exclusive=None))
        for month in range(7, 11):
            days = monthrange(2026, month)[1]
            for day in range(1, days+1):
                when = date(2026, month, day)
                if scope == "westhaven" and when == date(2026, 9, 18):
                    continue
                visits = 40+10*i+(day%5)*3 if when.weekday()<5 else 20+5*i
                if scope == "meadow" and when == date(2026, 8, 16):
                    visits = 0
                wait = waiting+(10-month)*2
                occupied = round(beds*(occupancy-(10-month)*2)/100)
                emergency = 15+4*i+day%7
                scheduled = visits+5+day%3
                row = dict(_id=f"cedar_{scope}_{when}", company_id="cedar", scope_id=scope, asset_id=name,
                    record_id=f"cedar_{scope}_{when}", activity_date=when.isoformat(),
                    visits=visits, wait_minutes=visits*wait, available_bed_days=beds,
                    occupied_bed_days=occupied, emergency_visits=emergency,
                    emergency_wait_minutes=emergency*(35+5*i+day%4), admissions=8+i+day%4,
                    discharges=7+i+day%5, scheduled_appointments=scheduled,
                    cancelled_appointments=2+i%3, revision=1, deleted=False)
                tables["activity"].append(row)
                if scope == "riverside" and month == 10 and day == 12:
                    # The first report over-counted waiting; revision 2 restores the correct value.
                    tables["activity"][-1] = {**row, "wait_minutes": row["wait_minutes"]+300}
                    tables["activity"].append({**row, "_id":row["_id"]+"_r2", "revision":2})
                if scope == "hillview" and month == 10 and day == 15:
                    duplicate = {**row, "record_id":row["record_id"]+"_withdrawn", "_id":row["_id"]+"_withdrawn"}
                    tables["activity"].extend([duplicate, {**duplicate, "_id":duplicate["_id"]+"_r2",
                                                           "revision":2, "deleted":True}])
            missing = scope == "westhaven" and month == 9
            tables["coverage"].append(dict(_id=f"cedar_{scope}_2026-{month:02}", company_id="cedar", scope_id=scope,
                asset_id=name, period_start=f"2026-{month:02}-01", period_end_exclusive=f"2026-{month+1:02}-01",
                expected_days=days, received_days=days-int(missing), status="incomplete" if missing else "complete",
                data_version="cedar-v2"))
    definitions = [
        ("measure", "Average outpatient waiting time", "wait_minutes", "visits", 1, "minutes per visit",
         "Total outpatient waiting minutes divided by outpatient visits. Combine totals before dividing."),
        ("occupancy", "Hospital bed occupancy", "occupied_bed_days", "available_bed_days", 100, "%",
         "Occupied bed-days divided by available staffed bed-days, times 100. This is occupancy, not outpatient attendance."),
        ("visits", "Outpatient visits", "visits", None, 1, "visits", "Total recorded outpatient visits."),
        ("emergency_wait", "Average emergency waiting time", "emergency_wait_minutes", "emergency_visits", 1, "minutes per visit",
         "Total emergency waiting minutes divided by emergency visits. This differs from outpatient waiting time."),
        ("emergency_visits", "Emergency visits", "emergency_visits", None, 1, "visits", "Total recorded emergency visits."),
        ("admissions", "Hospital admissions", "admissions", None, 1, "admissions", "Total admissions during the period."),
        ("discharges", "Hospital discharges", "discharges", None, 1, "discharges", "Total discharges during the period."),
        ("cancellations", "Appointment cancellation rate", "cancelled_appointments", "scheduled_appointments", 100, "%",
         "Cancelled appointments divided by scheduled appointments, times 100. Remaining appointments may include no-shows; do not equate them with visits."),
    ]
    for suffix, title, num, den, scale, unit, text in definitions:
        tables["documents"].append(dict(_id="cedar_"+suffix, document_id="cedar_"+suffix, company_id="cedar",
            scope_ids=scopes, title=title, text=text+" A zero denominator has no defined rate. No patient details or causal evidence are supplied.",
            status="approved", version="v2", valid_from="2026-07-01", source=f"cedar/{suffix}.md",
            measure=dict(group="hospital", numerator=num, denominator=den, scale=scale, unit=unit,
                         version="v2", minimum_input=0)))
    for suffix, title, text in [
        ("tasks", "Hospital operations questions",
         "Count hospitals; compare hospital occupancy, outpatient or emergency waiting time and visits, admissions, discharges and appointment cancellations. Summarize trends and totals over the available July–October 2026 records. No diagnoses, treatments, patient information or proven causes are available."),
        ("coverage", "Hospital reporting coverage and revisions",
         "Fictional operational data for July–October 2026. October is complete for six hospitals. Westhaven lacks 18 September; do not treat a missing day as zero. Meadow recorded zero outpatient visits on 16 August. Use the latest revision of each record and exclude withdrawn entries. Riverside has a corrected October posting; Hillview has a withdrawn duplicate. These counts concern activity, not unique patients."),
    ]:
        tables["documents"].append(dict(_id="cedar_"+suffix, document_id="cedar_"+suffix, company_id="cedar",
            scope_ids=scopes, title=title, text=text, status="approved", version="v2",
            valid_from="2026-07-01", source=f"cedar/{suffix}.md", measure=None))
    for name, values in tables.items():
        save(name, values)
    cases = read("cases")
    for case in cases:
        if case["case_id"] == "hospital_wait":
            case["expected_values"] = [[h[1], h[4]] for h in sorted(HOSPITALS, key=lambda h:h[4], reverse=True)]
    save("cases", cases)
    manifest = read("manifest")
    manifest.update(records=len(tables["activity"]), assets=len(tables["assets"]), scopes=len(tables["scopes"]))
    manifest["hospital_release"] = dict(version="cedar-v2", hospitals=6, period="2026-07-01 through 2026-10-31",
                                       kind="fictional deterministic demo data")
    save("manifest", manifest)


if __name__ == "__main__":
    prepare()
