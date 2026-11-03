"""Live API flow for a previously unseen client with only data and access settings."""
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import httpx
from console.services import running_services


@skipUnless(os.getenv("FARO_RUN_LIVE_TESTS")=="1","Starts APIs and calls paid models")
class CompassHttpTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        root=Path(cls.temp.name)
        (root/"users.json").write_text(json.dumps([
            dict(user_id="new_user",company_id="new_client",scope_ids=["allowed"],permission_version="v1",status="active"),
            dict(user_id="restricted",company_id="new_client",scope_ids=[],permission_version="v1",status="active")]))
        with sqlite3.connect(root/"bookings.sqlite") as db:
            db.execute("CREATE TABLE stays (property TEXT, booked_nights INTEGER)")
            db.executemany("INSERT INTO stays VALUES (?,?)",[("A",3),("A",4),("B",2)])
        (root/"connections.json").write_text(json.dumps([dict(company="new_client",scopes=["allowed"],file="bookings.sqlite")]))
        settings=patch.dict(os.environ,FARO_DATA_PATH=str(root),FARO_CONNECTOR_ROOT=str(root),
            FARO_COLLECTION_PATH=str(root/"collection"),FARO_DOCUMENT_PATH=str(root/"copies"))
        settings.start();cls.addClassCleanup(settings.stop)
        services=running_services();cls.urls=services.__enter__();cls.addClassCleanup(services.__exit__,None,None,None)
        cls.client=httpx.Client(timeout=180,trust_env=False);cls.addClassCleanup(cls.client.close)

    def ask(self,user,question,**extra):
        return self.client.post(self.urls["compass"]+"/v1/questions",json=dict(user_id=user,question=question,**extra))

    def test_new_client_just_data_no_company_setup(self):
        result=self.ask("new_user","How many booked nights are recorded in total?")
        self.assertEqual(result.status_code,200,result.text)
        response=result.json();print(json.dumps(response,indent=2),flush=True)
        self.assertEqual(response["verification"]["status"],"verified",response)
        self.assertIn("9",response["answer"]["text"])
        self.assertNotIn("company_information",response)
        self.assertTrue(response["answer"]["documents"])
        self.assertEqual(set(self.urls),{"gate","connector","thread","scout","signal","guide","bridge","shield","voice","compass"})

    def test_denied_user_and_empty_access(self):
        self.assertEqual(self.ask("missing","Count bookings").status_code,403)
        result=self.ask("restricted","Count bookings").json()
        self.assertEqual(result["decision"]["action"],"Unsupported")
        self.assertFalse(result["sources"]["items"])

    def test_clarification_keeps_original_question(self):
        first=self.ask("new_user","Compare the properties. Ask me what I want to compare before proceeding.").json()
        self.assertEqual(first["decision"]["action"],"Ask",first)
        second=self.ask("new_user","Total booked nights by property, highest first.",conversation_id=first["conversation_id"]).json()
        self.assertEqual(second["verification"]["status"],"verified",second)
        self.assertIn("7",second["answer"]["text"])
        self.assertIn("2",second["answer"]["text"])
        print(json.dumps(dict(first=first["followup"],reply=second["answer"]),indent=2),flush=True)
