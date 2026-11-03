"""Actual local HTTP, three real source files; no model needed for these checks."""
from pathlib import Path
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
import httpx
from openpyxl import load_workbook
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import Read, Finding, Link
from shield.verifier import Verifier as Shield
from shield.verifier_input import VerifierInput as ShieldRequest
from bridge.source import execute, catalogue, snapshot_id

DEMO=Path(__file__).resolve().parents[3]
SCOPES=["harbor_north","harbor_south"]
VIEW="operations/current_events"
SHEET="allocation/Assignments"
NOTE="operations_note/pages"


class SourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=TemporaryDirectory()
        cls.root=Path(cls.tmp.name)
        with socket.socket() as s:
            s.bind(("127.0.0.1",0));s.listen()
            cls.url=f"http://127.0.0.1:{s.getsockname()[1]}"
            cls.server=subprocess.Popen([sys.executable,"-m","uvicorn","connector_api.infer:app","--fd",str(s.fileno()),
                "--log-level","error","--no-access-log"],pass_fds=(s.fileno(),),env={**os.environ,"FARO_CONNECTOR_ROOT":cls.tmp.name,"FARO_DOCUMENT_PATH":cls.tmp.name+"/saved"})
        cls.setting=patch.dict(os.environ,FARO_CONNECTOR_URL=cls.url);cls.setting.start()
        cls.addClassCleanup(cls.stop_server)
        for _ in range(100):
            try:
                if httpx.get(cls.url+"/openapi.json",timeout=1).is_success:return
            except httpx.RequestError:pass
            time.sleep(.1)
        raise RuntimeError("Connector did not start")

    @classmethod
    def stop_server(cls):
        cls.setting.stop();cls.server.terminate();cls.server.wait(5);cls.tmp.cleanup()

    def setUp(self):
        shutil.copytree(DEMO/"connector/fixtures",self.root,dirs_exist_ok=True)
        self.request=BridgeInput(company_id="harbor",permitted_scope_ids=SCOPES,definition_ids=[],question="Rank the berths in October")
        self.data=DEMO/"local_data/demo_dataset"
        self.read=Read(source=VIEW,group="",member_ids=[],scope_ids=[],start=None,end_exclusive=None,
            link=Link(source=SHEET,left_field="ticket",right_field="Work reference"),
            expression="df.query(\"code == 'I' and period == '2026-10'\").groupby('Berth')['minutes'].sum().div(60).sort_values(ascending=False)")

    def api(self,action,**kw):
        return httpx.post(self.url+"/v1/sources",json={"company_id":"harbor","permitted_scope_ids":SCOPES,"action":action,**kw})

    def test_discover_inspect_project_and_trace_all_formats(self):
        self.assertEqual({x["kind"] for x in self.api("discover").json()["items"]},{"sqlite","xlsx","pdf"})
        for item,field,ref in [(VIEW,"minutes","operations.sqlite#current_events:"),
                               (SHEET,"Work reference","allocation.xlsx#Assignments!"),(NOTE,"text","operations_note.pdf#page 1")]:
            with self.subTest(item=item):
                inspect=self.api("inspect",item=item).json()
                self.assertIn(field,inspect["items"][0]["fields"])
                read=self.api("read",item=item,fields=[field]).json()
                self.assertEqual(set(read["rows"][0]),{field})
                self.assertTrue(read["references"][0].startswith(ref))
                self.assertEqual(read["items"][0]["version"],inspect["items"][0]["version"])

    def test_documents_preserve_the_exact_read_version(self):
        from hashlib import sha256
        from urllib.parse import urlparse, unquote
        for item in (VIEW, SHEET, NOTE):
            result=self.api("read",item=item).json()
            document=result["document"]
            saved=Path(unquote(urlparse(document["uri"]).path))
            self.assertEqual(sha256(saved.read_bytes()).hexdigest(),document["version"])
            self.assertEqual(document["version"],result["items"][0]["version"])
        first=self.api("read",item=VIEW).json()["document"]
        with sqlite3.connect(self.root/"operations.sqlite") as db:
            db.execute("UPDATE event_revisions SET minutes=100 WHERE ticket='N-17'")
        second=self.api("read",item=VIEW).json()["document"]
        self.assertNotEqual(first["uri"],second["uri"])
        self.assertEqual(sha256(Path(unquote(urlparse(first["uri"]).path)).read_bytes()).hexdigest(),first["version"])

    def test_scope_and_company_filter_discovery_and_direct_reads(self):
        for access in ({"company_id":"different"},{"permitted_scope_ids":["harbor_north"]}):
            self.assertEqual(self.api("discover",**access).json()["items"],[])
            self.assertEqual(self.api("read",item=VIEW,**access).status_code,403)
        self.assertEqual(self.api("read",item="../other.sqlite").status_code,403)

    def test_reconcile_results_and_invalidate_after_correction(self):
        e=execute(self.data,self.request,self.read)
        self.assertEqual([(r["Berth"],r["value"]) for r in e.rows],[("S1",115),("N1",100),("N2",86),("S2",71)])
        self.assertEqual(len(e.source_evidence),2)
        e.findings=[Finding(text="S1 leads at 115 hours.",evidence_ids=[1])]
        e.catalogue_version=snapshot_id(catalogue(self.data,self.request))
        with sqlite3.connect(self.root/"operations.sqlite") as db:
            db.execute("INSERT INTO event_revisions VALUES ('N-17',3,'I',7560,0,'2026-10')")
        updated=execute(self.data,self.request,self.read)
        self.assertEqual(updated.rows[0],{"Berth":"N1","value":126})
        model=Mock()
        result=Shield(self.data,model).verify(ShieldRequest(**self.request.model_dump(),evidence=e))
        self.assertEqual(result.status,"withheld");model.predict.assert_not_called()

    def test_missing_or_ambiguous_assignment_blocks_join(self):
        for duplicate in (False,True):
            shutil.copy(DEMO/"connector/fixtures/allocation.xlsx",self.root/"allocation.xlsx")
            wb=load_workbook(self.root/"allocation.xlsx");ws=wb.active
            if duplicate:ws.append([v.value for v in ws[2]])
            else:ws.delete_rows(2)
            wb.save(self.root/"allocation.xlsx")
            with self.assertRaisesRegex(ValueError,"unmatched|ambiguous"):
                execute(self.data,self.request,self.read)
            reverse=self.read.model_copy(update={"source":SHEET,"link":Link(source=VIEW,left_field="Work reference",right_field="ticket")})
            if not duplicate:
                with self.assertRaisesRegex(ValueError,"unmatched"):
                    execute(self.data,self.request,reverse)

    def test_unrelated_schema_discovered_without_business_mapping(self):
        with sqlite3.connect(self.root/"operations.sqlite") as db:
            db.execute('CREATE TABLE bookings (booking_id TEXT PRIMARY KEY, nights INTEGER)')
            db.execute("INSERT INTO bookings VALUES ('B1',4)")
        result=self.api("read",item="operations/bookings",fields=["nights"]).json()
        self.assertEqual(result["rows"],[{"nights":4}])
        self.assertIn("booking_id=B1",result["references"][0])
