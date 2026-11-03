"""Prepare the sector examples in Faro's shared record format. Business choices belong here."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "local_data/demo_dataset"


def prepare():
    def read(name):
        return json.loads((ROOT / f"{name}.json").read_text())

    def save(name, rows):
        (ROOT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")

    companies, users, scopes, docs, assets, activity, coverage, agreements = (
        read(name) for name in ("companies", "users", "terminals", "documents", "assets", "activity", "coverage", "agreements"))
    for company in companies:
        key = company["company_id"]
        company["task_document_ids"] = [f"{key}_supported_tasks_v1"]
    for doc in docs:
        if doc["document_id"] == f'{doc["company_id"]}_downtime_v1':
            doc["measure"] = dict(group="crane", numerator="downtime_hours", denominator=None, scale=1, unit="hours", version="v1")
    companies.append(dict(company_id="retail", name="Sample Retail", timezone="Europe/Amsterdam",
                          data_version="retail-v1", definition_version="v1", task_document_ids=["retail_tasks"]))
    scope = dict(company_id="retail", terminal_id="retail_region")
    scopes.append(dict(**scope, name="Retail region", aliases=[]))
    users.append(dict(user_id="sam", company_id="retail", terminal_ids=["retail_region"], permission_version="v1", status="active"))
    for key, title, text, measure in [
        ("retail_tasks","Supported questions","Compare stores by sales or return rate. Product rankings and causes are not supported.",None),
        ("retail_rate","Store return rate","Store return rate is 100 times total returned units divided by total units sold in the period. A zero denominator gives no rate.",
         dict(group="store", numerator="returned", denominator="sold", scale=100, unit="%", version="v1")),
        ("retail_sales","Store sales","Store sales means total units sold.",dict(group="store", numerator="sold", denominator=None, scale=1, unit="units", version="v1"))]:
        docs.append(dict(company_id="retail", terminal_ids=["retail_region"], document_id=key, title=title,text=text,
                         status="approved", version="v1", valid_from="2026-10-01", source=f"retail/{key}.md",measure=measure))
    for store, returned, sold in [("East",20,1000),("West",5,50)]:
        assets.append(dict(**scope,asset_id=store,asset_type="store",active_from="2026-10-01",active_until_exclusive=None))
        for day in range(1,32):
            when=f"2026-10-{day:02}"
            activity.append(dict(**scope,asset_id=store,record_id=f"{store}_{when}",activity_date=when,
                                 returned=returned if day==1 else 0,sold=sold if day==1 else 0,revision=1,deleted=False))
        coverage.append(dict(**scope,asset_id=store,period_start="2026-10-01",period_end_exclusive="2026-11-01",
                             expected_days=31,received_days=31,status="complete",data_version="retail-v1"))
    for path in sorted((ROOT.parent / "sector_examples").glob("*.json")):
        client = json.loads(path.read_text())
        cid, group = client["company_id"], client["group"]
        locations = [m["scope"] for m in client["members"]]
        companies.append(dict(company_id=cid, name=client["name"], timezone=client["timezone"], data_version=f"{cid}-v1",
                              definition_version="v1", task_document_ids=[f"{cid}_tasks"]))
        for user, allowed in client["users"].items():
            users.append(dict(user_id=user, company_id=cid, terminal_ids=allowed, permission_version="v1", status="active"))
        measure = {k:client[k] for k in ("group","numerator","denominator","scale","unit")}
        for suffix,title,text,operation in [("tasks","Supported questions",client["tasks"],None),
                                           ("measure",client["title"],client["definition"],dict(measure,version="v1"))]:
            docs.append(dict(company_id=cid,terminal_ids=locations,document_id=f"{cid}_{suffix}",title=title,text=text,
                             status="approved",version="v1",valid_from="2026-10-01",source=f"{cid}/{suffix}.md",measure=operation))
        for m in client["members"]:
            scope = dict(company_id=cid,terminal_id=m["scope"])
            scopes.append(dict(**scope,name=f'{m["id"]}, {m["country"]}',aliases=[m["id"]]))
            assets.append(dict(**scope,asset_id=m["id"],asset_type=group,active_from="2026-10-01",active_until_exclusive=None))
            for day in range(1,32):
                when = f"2026-10-{day:02}"
                activity.append(dict(**scope,asset_id=m["id"],record_id=f'{cid}_{m["scope"]}_{when}',activity_date=when,
                                     **m["daily"],revision=1,deleted=False))
            coverage.append(dict(**scope,asset_id=m["id"],period_start="2026-10-01",period_end_exclusive="2026-11-01",
                                 expected_days=31,received_days=31,status="complete",data_version=f"{cid}-v1"))
    for name, rows in [("companies",companies),("users",users),("scopes",scopes),("documents",docs),("assets",assets),
                       ("activity",activity),("coverage",coverage),("agreements",agreements)]:
        for row in rows:
            if "_id" not in row:
                identifiers = {"companies":"company_id","users":"user_id","scopes":"terminal_id","documents":"document_id",
                               "assets":"asset_id","activity":"record_id"}
                row["_id"] = (f'{row["company_id"]}_{row["asset_id"]}_{row["period_start"]}' if name == "coverage"
                              else row[identifiers[name]])
            if name == "documents" and row.get("measure"):
                row["measure"]["minimum_input"] = 0
            for before,after in [("terminal_ids","scope_ids"),("terminal_id","scope_id")]:
                if before in row: row[after]=row.pop(before)
        save(name, rows)
    cases = read("cases")
    for cid,user,question,outcome,expected in [
        ("retail_rate","sam","Which stores had the highest return rate in October 2026?","ANSWER",[["West",10],["East",2]]),
        ("hospital_wait","hospital_ops","Rank all my hospitals by highest average outpatient waiting time in October 2026.","ANSWER",[["Hillview Hospital",45],["Riverside Hospital",30]]),
        ("hotel_worldwide","hotel_hq","Rank all my hotels worldwide by lowest occupancy rate in October 2026.","ANSWER",[["Tokyo Bay",70],["Madrid Central",80],["Mexico City Plaza",90]]),
        ("hotel_local","madrid_manager","Show the October 2026 occupancy rate for Madrid Central, highest first.","ANSWER",[["Madrid Central",80]]),
        ("hotel_denied","madrid_manager","Show the October 2026 occupancy rate for Tokyo Bay, highest first.","NO_FIGURES",[])]:
        cases.append(dict(_id=cid,case_id=cid,user_id=user,question=question,expected_outcome=outcome,expected_values=expected,scenario=None))
    save("cases",cases)
    manifest=read("manifest")
    manifest.pop("not_implemented",None)
    manifest["scope"]="Port operations, retail stores, hospital operations and an international hotel chain."
    manifest["cases"]=len(cases)
    manifest.update(companies=len(companies),users=len(users),records=len(activity),assets=len(assets),scopes=len(scopes))
    save("manifest",manifest)
