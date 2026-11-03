"""Expose the existing fictional records as native JSON sources for the demo."""
import json
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]


def create():
    data = DEMO / "local_data/demo_dataset"
    root = DEMO / "connector/fixtures"
    grants = [g for g in json.loads((root/"connections.json").read_text()) if g["file"] not in {"harbor.json","pacific.json","strait.json","retail.json","cedar.json","meridian.json"}]
    scopes = json.loads((data/"scopes.json").read_text())
    for company in sorted({s["company_id"] for s in scopes}):
        tables = {name:[row for row in json.loads((data/f"{name}.json").read_text()) if row["company_id"]==company]
                  for name in ("assets","activity","coverage")}
        (root/f"{company}.json").write_text(json.dumps(tables,ensure_ascii=False,indent=2)+"\n")
        grants.append(dict(company=company, scopes=[s["scope_id"] for s in scopes if s["company_id"]==company],
                           file=f"{company}.json",scope_field="scope_id"))
    (root/"connections.json").write_text(json.dumps(grants,indent=2)+"\n")


if __name__ == "__main__":
    create()
