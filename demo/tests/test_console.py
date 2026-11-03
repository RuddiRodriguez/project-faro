"""Exercise the actual command, APIs, model calls and saved cache."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Starts ten APIs and calls the configured model")
class ConsoleTests(unittest.TestCase):
    def test_followup_and_repeat(self):
        ranking = "Rank North Terminal cranes by highest downtime last month."
        messages = ["maria", "Which cranes performed badly last month?",
                    "North Terminal, downtime, highest first.", "/new", ranking, "/new", ranking, "/quit"]
        with TemporaryDirectory() as folder:
            run = subprocess.run([sys.executable, "console.py", "--test"],
                cwd=Path(__file__).resolve().parents[1], input="\n".join(messages) + "\n",
                text=True, capture_output=True, timeout=420,
                env={**os.environ, "FARO_COLLECTION_PATH": folder})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("All ten APIs are ready.", run.stdout)
        self.assertIn("Result: Ask", run.stdout)
        self.assertEqual(run.stdout.count("Result: verified"), 3, run.stdout)
        first, repeat = run.stdout.split("New conversation.")[-2:]
        self.assertEqual(first.split("Faro: ", 1)[1].split("Test:")[0],
                         repeat.split("Faro: ", 1)[1].split("Test:")[0])
        self.assertIn("Bridge", repeat.split("Reused: ", 1)[1].splitlines()[0])

    def test_choice_followups_and_switching_accounts(self):
        messages = ["unknown_demo_account", "maria", "Which cranes performed badly", "Idle time",
                    "Rank North Terminal cranes by highest downtime last month.", "/logout", "hospital_ops",
                    "Rank all my hospitals by highest average outpatient waiting time in October 2026.", "/quit"]
        from compass.data_collection import DataCollection
        with TemporaryDirectory() as folder:
            run = subprocess.run([sys.executable, "console.py", "--test"],
                cwd=Path(__file__).resolve().parents[1], input="\n".join(messages) + "\n",
                text=True, capture_output=True, timeout=420,
                env={**os.environ, "FARO_COLLECTION_PATH": folder})
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("User not found or account is disabled", run.stdout)
            store = DataCollection(folder)
            def turns(company):
                headers = list((Path(folder)/company/"conversations").glob("*.parquet"))
                return [store.read_conversation(company, h.stem)["turns"] for h in headers]
            harbor = sorted(turns("harbor"),key=len)
            direct, (first, chosen) = harbor
            self.assertEqual(first["status"],"Ask")
            self.assertEqual(chosen["status"],"Unsupported")
            self.assertIsNone(chosen["response"]["followup"])
            self.assertFalse(chosen["cache"])
            self.assertEqual(direct[0]["status"],"verified",run.stdout)
            self.assertEqual(direct[0]["number"],1)
            hospital, = turns("cedar")[0]
            self.assertEqual(hospital["status"],"verified")
