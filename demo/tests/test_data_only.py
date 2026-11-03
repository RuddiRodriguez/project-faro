"""Exercise the data-only boundary through the actual console."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from compass.data_collection import DataCollection


@unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Calls the configured model")
class DataOnlyTests(unittest.TestCase):
    def test_clarification_is_the_only_continuation(self):
        messages = ["hospital_ops", "What can you answer?", "Which hospitals performed worst in October 2026?",
                    "Use average outpatient waiting time, highest first, for all hospitals.",
                    "Rank all my hospitals by highest average outpatient waiting time in October 2026.", "/quit"]
        with TemporaryDirectory() as folder:
            run = subprocess.run([sys.executable,"console.py","--test"], input="\n".join(messages)+"\n",
                cwd=Path(__file__).resolve().parents[1], capture_output=True,text=True,timeout=420,
                env={**os.environ,"FARO_COLLECTION_PATH":folder})
            self.assertEqual(run.returncode,0,run.stderr)
            store = DataCollection(folder)
            docs = {d["original_question"]:d["turns"] for p in (Path(folder)/"cedar/conversations").glob("*.parquet")
                    for d in [store.read_conversation("cedar",p.stem)]}
            self.assertEqual(set(docs),{messages[1],messages[2],messages[4]},run.stdout)
            unsupported, = docs[messages[1]]
            self.assertEqual(unsupported["status"], "Unsupported")
            self.assertIsNone(unsupported["response"]["followup"])
            self.assertEqual(unsupported["response"]["answer"]["text"],"I can only answer questions about your company data.")
            asked, clarified = docs[messages[2]]
            self.assertEqual(asked["status"],"Ask",run.stdout)
            self.assertFalse(clarified["cache"])
            direct, = docs[messages[4]]
            for t in (clarified,direct):
                self.assertEqual(t["status"],"verified",run.stdout)
                self.assertEqual([row["value"] for row in t["response"]["evidence"]["rows"]],[45,30])
                self.assertIsNone(t["response"]["followup"])
            print(run.stdout)

    def test_two_clarifications_stay_on_one_request(self):
        messages = ["hospital_ops", "Which of all my hospitals performed worst?",
                    "Average outpatient waiting time, highest first.", "October 2026.", "/quit"]
        with TemporaryDirectory() as folder:
            run = subprocess.run([sys.executable,"console.py","--test"],input="\n".join(messages)+"\n",
                cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=420,
                env={**os.environ,"FARO_COLLECTION_PATH":folder})
            print(run.stdout)
            self.assertEqual(run.returncode,0,run.stderr)
            header, = (Path(folder)/"cedar/conversations").glob("*.parquet")
            turns = DataCollection(folder).read_conversation("cedar",header.stem)["turns"]
            self.assertEqual([t["status"] for t in turns], ["Ask","Ask","verified"],run.stdout)
            for t in turns[:2]:
                self.assertEqual(t["response"]["followup"]["followup_text"].count("?"),1)
            self.assertIn("waiting",turns[1]["response"]["rewrite"]["question"].lower())
            self.assertEqual(turns[2]["response"]["evidence"]["read"]["start"],"2026-10-01")
            self.assertEqual([v["value"] for v in turns[2]["response"]["evidence"]["rows"]],[45,30])
            self.assertFalse(turns[1]["cache"] or turns[2]["cache"])
