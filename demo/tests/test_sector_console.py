"""Opt-in live smoke test: one real console, four sectors and persisted model summaries."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase,skipUnless

from compass.data_collection import DataCollection

DEMO=Path(__file__).resolve().parents[1]
CASES=[
    ("maria","harbor","Which berths had the most crane idle hours last month?"),
    ("sam","retail","How many units did all our stores sell in October 2026?"),
    ("hospital_ops","cedar","Compare hospital bed occupancy in October 2026, highest first."),
    ("hotel_hq","meridian","How many hotels do we have?"),
]


@skipUnless(os.getenv("FARO_RUN_LIVE_TESTS")=="1","Runs the console and paid models")
class SectorConsoleTests(TestCase):
    def test_four_sectors_and_saved_explanations(self):
        with TemporaryDirectory() as temp:
            folder=Path(os.getenv("FARO_TEST_COLLECTION_PATH",temp))
            messages=[]
            for i,(user,company,question) in enumerate(CASES):
                if i:messages.append("/logout")
                messages.extend([user,question])
            messages.append("/quit")
            run=subprocess.run([sys.executable,"console.py","--test"],cwd=DEMO,
                input="\n".join(messages)+"\n",text=True,capture_output=True,timeout=720,
                env={**os.environ,"FARO_COLLECTION_PATH":str(folder)})
            print(run.stdout,flush=True)
            self.assertEqual(run.returncode,0,run.stderr)
            store=DataCollection(folder)
            summaries=[]
            for user,company,question in CASES:
                turns=[t for p in (folder/company/"conversations").glob("*.parquet")
                       for t in store.read_conversation(company,p.stem)["turns"] if t["message"]==question]
                self.assertEqual(len(turns),1,question)
                turn=turns[0]
                self.assertEqual(turn["status"],"verified",(question,turn.get("response")))
                for call in turn["model_explanations"]:
                    self.assertTrue(call["explanations"],call)
                    self.assertTrue(call["explanations"][-1]["initial_analysis"])
                    self.assertTrue(call["explanations"][-1]["reasoning"])
                response=turn["response"]
                evidence=response["evidence"]
                for observation in [evidence,*evidence["supporting"]]:
                    self.assertEqual(observation["company_id"],company)
                if company=="harbor":
                    self.assertEqual({d["name"] for d in response["answer"]["documents"]},
                                     {"operations.sqlite","operations_note.pdf","allocation.xlsx"})
                    self.assertIn("115",response["answer"]["text"])
                elif company=="retail":
                    self.assertTrue(any(r.get("value")==1050 for obs in [evidence,*evidence["supporting"]] for r in obs["rows"]))
                elif company=="cedar":
                    self.assertIn("95",response["answer"]["text"])
                    self.assertIn("65",response["answer"]["text"])
                else:
                    self.assertIn("3",response["answer"]["text"])
                summaries.append(dict(company=company,question=question,status=turn["status"],
                    answer=response["answer"]["text"],elapsed_ms=turn["elapsed_ms"],
                    model_explanations=turn["model_explanations"]))
            (folder/"sector_results.json").write_text(json.dumps(summaries,indent=2))


@skipUnless(os.getenv("FARO_RUN_LIVE_TESTS")=="1","Runs the clarification console and paid models")
class ClarificationConsoleTests(TestCase):
    def test_guide_and_thread_keep_the_user_choice(self):
        with TemporaryDirectory() as temp:
            folder=Path(os.getenv("FARO_TEST_COLLECTION_PATH",temp))/"clarification"
            first="I want to compare cranes. Please ask me which indicator to use before reading their performance data."
            reply="Total downtime, North Terminal, October 2026, highest first."
            run=subprocess.run([sys.executable,"console.py","--test"],cwd=DEMO,
                input="\n".join(["maria",first,reply,"/quit"])+"\n",
                text=True,capture_output=True,timeout=360,
                env={**os.environ,"FARO_COLLECTION_PATH":str(folder)})
            print(run.stdout,flush=True)
            self.assertEqual(run.returncode,0,run.stderr)
            store=DataCollection(folder)
            turns=[t for p in (folder/"harbor/conversations").glob("*.parquet")
                   for t in store.read_conversation("harbor",p.stem)["turns"]]
            self.assertEqual([t["status"] for t in turns],["Ask","verified"])
            self.assertTrue(turns[0]["response"]["followup"]["initial_analysis"])
            self.assertTrue(turns[0]["response"]["followup"]["reasoning"])
            self.assertTrue(turns[1]["response"]["rewrite"]["reasoning"])
            self.assertIn("North",turns[1]["response"]["rewrite"]["question"])
            for t in turns:
                for call in t["model_explanations"]:
                    self.assertTrue(call["explanations"],call)
            (folder/"clarification_results.json").write_text(json.dumps(
                [dict(question=t["message"],status=t["status"],response=t["response"],
                      model_explanations=t["model_explanations"]) for t in turns],indent=2))
