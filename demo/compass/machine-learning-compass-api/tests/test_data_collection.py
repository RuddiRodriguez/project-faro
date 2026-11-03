import sqlite3
import unittest
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pandas as pd
from api_objects.faro.gate.output.gate_output import GateOutput
from api_objects.faro.signal.output.signal_output import SignalOutput
from compass.collection_schema import COLUMNS, field_origins
from compass.data_collection import DataCollection, TurnCache, now
from compass.orchestrator_input import OrchestratorInput


class CollectionTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = DataCollection(tmp.name)
        self.access = GateOutput(user_id="maria",company_id="harbor",permitted_scope_ids=["north"],permission_version="v1")

    def test_cache_origin_isolation_expiry_and_version(self):
        model = SignalOutput
        cache = TurnCache(self.store,self.access,{"version":"v1"},[],"first-turn")
        call = Mock(return_value=model(action="Ask",missing_choice="measure"))
        args = ("Signal", {"question":"Which ones?"}, model, call)
        cache.ai(*args)
        other_turn = TurnCache(self.store,self.access,{"version":"v1"},[],"second-turn")
        other_turn.ai(*args)
        self.assertEqual(call.call_count,1)
        self.assertEqual(other_turn.events[0]["produced_by_turn"],"first-turn")
        for change in ({"user_id":"luis"},{"company_id":"cedar"},{"permission_version":"v2"},{"permitted_scope_ids":[]}):
            isolated = TurnCache(self.store,self.access.model_copy(update=change),{"version":"v1"},[],"another")
            isolated.ai(*args)
            self.assertEqual(isolated.events[0]["result_source"],"fresh")
        key = cache.events[0]["key"]
        path = self.store.path("harbor","ai_cache",key)
        row = pd.read_parquet(path).to_dict("records")[0]
        for changes in [{"version":"old"},{"expires_at":now()-timedelta(seconds=1)}]:
            self.store.write(path,"ai_cache",[{**row,**changes}])
            self.assertEqual(self.store.fetch("harbor","ai",key,model),(None,None))

    def test_failed_model_call_creates_no_entry(self):
        cache = TurnCache(self.store,self.access,{},[],"failed")
        with self.assertRaises(RuntimeError):
            cache.ai("Signal","question",SignalOutput,Mock(side_effect=RuntimeError("offline")))
        self.assertFalse(self.store.path("harbor","ai_cache",cache.events[0]["key"]).exists())

    def test_field_guide_and_proposed_sql_have_matching_columns(self):
        ddl = Path(__file__).resolve().parents[4] / "docs/data_collection_schema.sql"
        with sqlite3.connect(":memory:") as db:
            db.executescript(ddl.read_text())
            for table,fields in COLUMNS.items():
                self.assertEqual([r[1] for r in db.execute(f"PRAGMA table_info({table})")],[f[0] for f in fields])
        guide={(t,p):s for t,p,s in field_origins()}
        for table,fields in COLUMNS.items():
            for column,_,_ in fields:self.assertTrue(guide[table,column])

    def test_changed_permissions_block_saved_history(self):
        request=OrchestratorInput(user_id="maria",question="First question")
        with self.store.conversation(request,self.access) as doc:
            doc["turns"].append(dict(_id="one",number=1,message=request.question,language=None,
                created_at=now().isoformat(),status="failed",cache=[]))
            self.store.save_conversation(doc)
        request.conversation_id=doc["_id"]
        with self.assertRaises(PermissionError):
            with self.store.conversation(request,self.access.model_copy(update={"permitted_scope_ids":[]})):
                self.fail("Conversation opened with changed access")

    def test_previous_answer_shares_only_the_verified_question_with_its_owner(self):
        request = OrchestratorInput(user_id="maria", question="Count my cranes")
        with self.store.conversation(request, self.access) as doc:
            doc["turns"].append(dict(_id="first", number=1, message=request.question, language=None,
                created_at=now().isoformat(), status="verified", cache=[],
                response={"rewrite":{"question":request.question}, "answer":{"text":"Private result"}}))
            self.store.save_conversation(doc)
        next_request = OrchestratorInput(user_id="maria", question="And per terminal?", previous_answer_id=doc["_id"])
        with self.store.conversation(next_request, self.access) as followup:
            self.assertEqual(followup["messages"], [{"role":"user","content":request.question}])
            self.assertEqual(followup["original_question"], next_request.question)
        for change in ({"user_id":"luis"}, {"permitted_scope_ids":[]}):
            with self.assertRaises(PermissionError):
                with self.store.conversation(next_request, self.access.model_copy(update=change)):
                    self.fail("Shared another account's context")
