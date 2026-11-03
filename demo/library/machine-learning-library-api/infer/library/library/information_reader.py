import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from library.information_reader_input import InformationReaderInput
from library.information_reader_output import InformationReaderOutput


class LibraryRequestError(ValueError):
    pass


class InformationReader:
    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)

    def _read(self, collection: str) -> list[dict]:
        return json.loads((self.data_path / f"{collection}.json").read_text())

    def read(self, information_reader_input: InformationReaderInput) -> InformationReaderOutput:
        company_id = information_reader_input.company_id
        company = next((item for item in self._read("companies")
                        if item["company_id"] == company_id), None)
        if company is None:
            raise LibraryRequestError("Company not found")

        company_scopes = [item for item in self._read("scopes")
                             if item["company_id"] == company_id]
        permitted = set(information_reader_input.permitted_scope_ids)
        if not permitted.issubset({item["scope_id"] for item in company_scopes}):
            raise LibraryRequestError("A permitted location or group does not belong to this company")

        scopes = [item for item in company_scopes if item["scope_id"] in permitted]
        documents = []
        for item in self._read("documents"):
            if item["company_id"] != company_id or item["status"] != "approved":
                continue
            visible_scopes = [value for value in item["scope_ids"] if value in permitted]
            if visible_scopes:
                documents.append({**item, "scope_ids": visible_scopes})

        agreements = [item for item in self._read("agreements")
                      if item["company_id"] == company_id
                      and item["scope_id"] in permitted
                      and item["status"] == "approved"]
        members = [a for a in self._read("assets") if a["company_id"] == company_id and a["scope_id"] in permitted]
        groups = {kind: [a["asset_id"] for a in members if a["asset_type"] == kind]
                  for kind in {a["asset_type"] for a in members}}
        tasks = [d["text"] for d in documents if d["document_id"] in company["task_document_ids"]]
        now = datetime.fromisoformat(self._read("manifest")["default_now_utc"])
        return InformationReaderOutput(supported_tasks=tasks, groups=groups,
                               reference_date=now.astimezone(ZoneInfo(company["timezone"])).date(), company=company, scopes=scopes,
                               documents=documents, agreements=agreements)
