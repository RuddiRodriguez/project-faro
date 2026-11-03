"""Sector-neutral stress cases. No paid model calls."""
import json
import os
import sqlite3
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import unquote,urlparse

from api_objects.faro.connector.input.connector_input import ConnectorInput
from bridge.source import run_read
from connector.source_reader import SourceReader


class SectorStressTests(TestCase):
    def test_unseen_companies_and_field_names_need_no_service_changes(self):
        cases = [
            ("logistics", "berth", "idle_minutes", [("A",60),("A",120),("B",30)]),
            ("healthcare", "unit", "visits", [("A",20),("A",30),("B",10)]),
            ("retail", "shop", "sold", [("A",7),("A",8),("B",4)]),
            ("hospitality", "property", "room_nights", [("A",90),("A",10),("B",50)]),
            ("recycling", "district", "recovered_kg", [("A",400),("A",600),("B",200)]),
            ("unseen", "unknown_label", "unknown_value", [("A",1),("A",2),("B",4)]),
        ]
        with TemporaryDirectory() as temp, patch.dict(os.environ,FARO_DOCUMENT_PATH=temp+"/copies"):
            root=Path(temp)
            grants=[]
            for company,label,value,rows in cases:
                with sqlite3.connect(root/f"{company}.sqlite") as db:
                    db.execute(f'CREATE TABLE records ("{label}" TEXT, "{value}" INTEGER)')
                    db.executemany("INSERT INTO records VALUES (?,?)", rows)
                grants.append(dict(company=company,scopes=["allowed"],file=f"{company}.sqlite"))
            (root/"connections.json").write_text(json.dumps(grants))
            reader=SourceReader(root)
            for company,label,value,rows in cases:
                with self.subTest(company=company):
                    request=ConnectorInput(company_id=company,permitted_scope_ids=["allowed"],action="discover")
                    items=reader.read(request).items
                    self.assertEqual(len(items),1)
                    self.assertEqual(items[0].fields,[label,value])
                    result=reader.read(request.model_copy(update={"action":"read","item":items[0].id}))
                    grouped=run_read(f"df.groupby('{label}')['{value}'].sum()",result.rows,[label,value])
                    self.assertEqual(grouped,[{label:"A","value":rows[0][1]+rows[1][1]},
                                              {label:"B","value":rows[2][1]}])
                    for other, *_ in cases:
                        if other!=company:
                            with self.assertRaises(PermissionError):
                                reader.read(request.model_copy(update={"action":"read","item":other+"/records"}))
                    doc=result.document
                    self.assertEqual(sha256(Path(unquote(urlparse(doc["uri"]).path)).read_bytes()).hexdigest(),doc["version"])

    def test_worker_refuses_private_attributes_and_invalid_results(self):
        rows=[{"label":"A","value":3}]
        for expression in [
            "df.__class__",
            "df['value']/0", "df.rename(columns={'label':'value'})",
        ]:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                run_read(expression,rows,["label","value"])

    def test_large_source_returns_all_rows(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ,FARO_DOCUMENT_PATH=temp+"/copies"):
            root=Path(temp)
            with sqlite3.connect(root/"data.sqlite") as db:
                db.execute("CREATE TABLE data (v INTEGER)")
                db.executemany("INSERT INTO data VALUES (?)",[(i,) for i in range(1001)])
            (root/"connections.json").write_text(json.dumps([dict(company="client",scopes=["scope"],file="data.sqlite")]))
            result=SourceReader(root).read(ConnectorInput(company_id="client",permitted_scope_ids=["scope"],action="read",item="data/data"))
            self.assertEqual(len(result.rows),1001)
            self.assertEqual(result.rows[-1],{"v":1000})
            self.assertEqual(len(result.references),1001)
            self.assertTrue((root/"copies").exists())
