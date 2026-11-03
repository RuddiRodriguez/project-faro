"""Replay Maria's eight original messages against the real console and live services."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from compass.data_collection import DataCollection


MESSAGES = [
    "how many cranes per terminal do we have ?",
    "from all terminals in which terminal the cranes performance better?",
    "lowest Downtime",
    "and what is the terminal with the lower Idle time",
    "what other data you hva in the catalogue?",
    "ok make an analysis of the perofmrance in general of the terminal south",
    "no make an anlysis in general you are free to choose i need to know what terminal is working better",
    "no , you are free to do any analysis you consider",
]


@unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Runs the eleven APIs and live models")
class MariaAnalysisTests(unittest.TestCase):
    def test_exact_conversation(self):
        with TemporaryDirectory() as temp:
            folder = Path(os.getenv("FARO_TEST_COLLECTION_PATH",temp))
            run = subprocess.run([sys.executable,"console.py","--test"], cwd=Path(__file__).resolve().parents[1],
                input="\n".join(["maria",*MESSAGES,"/quit"])+"\n", capture_output=True,text=True,timeout=750,
                env={**os.environ,"FARO_COLLECTION_PATH":str(folder)})
            print(run.stdout)
            self.assertEqual(run.returncode,0,run.stderr)
            store=DataCollection(folder)
            turns={t["message"]:t for f in (folder/"harbor/conversations").glob("*.parquet")
                   for t in store.read_conversation("harbor",f.stem)["turns"]}
            self.assertEqual(set(turns),set(MESSAGES))
            for i in (0,2,3,4,5,6,7):
                with self.subTest(message=MESSAGES[i]):
                    t=turns[MESSAGES[i]]
                    self.assertEqual(t["status"],"verified",t.get("response"))
                    r=t["response"]
                    self.assertIsNone(r["followup"])
                    self.assertTrue(r["verification"]["facts"]["findings"])
                    if i != 4:
                        self.assertTrue(r["evidence"]["record_ids"])
