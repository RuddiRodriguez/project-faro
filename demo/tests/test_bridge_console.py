"""Live console: no pre-filled plans or mocked service calls."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from compass.data_collection import DataCollection


@unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Starts ten APIs and calls the configured model")
class BridgeConsoleTests(unittest.TestCase):
    def test_count_history_and_total(self):
        count = "how many cranes do we have?"
        ranking = "Which cranes had the most downtime?"
        retail = "How many units did we sell across all our stores in October 2026?"
        messages = ["maria", count, "and how many per terminal?", ranking, "All time, across all my terminals.", "/logout", "sam", retail, "/quit"]
        with TemporaryDirectory() as temp:
            folder = Path(os.getenv("FARO_TEST_COLLECTION_PATH", temp))
            run = subprocess.run([sys.executable, "console.py", "--test"], cwd=Path(__file__).resolve().parents[1],
                input="\n".join(messages)+"\n", text=True, capture_output=True, timeout=420,
                env={**os.environ, "FARO_COLLECTION_PATH":str(folder)})
            print(run.stdout)
            self.assertEqual(run.returncode,0,run.stderr)
            self.check_results(folder, messages, run.stdout, run.stderr)

    def check_results(self, folder, messages, stdout, stderr):
        count, ranking, retail = messages[1], messages[3], messages[7]
        store = DataCollection(folder)
        docs = {doc["original_question"]:doc["turns"] for company in ("harbor", "retail")
                for f in (folder/company/"conversations").glob("*.parquet")
                for doc in [store.read_conversation(company, f.stem)]}
        # The first ranking may be useful immediately with disclosed dates, or it may need clarification.
        # The explicit all-history message must produce the same supported ranking in either path.
        initial = docs[ranking][0]
        self.assertIn(initial["status"], ("Ask","verified"), (initial.get("error"), stderr, stdout))
        if initial["status"]=="verified":
            self.assertTrue(initial["response"]["evidence"]["period"])
        final_turn = next(t for turns in docs.values() for t in turns if t["message"]==messages[4])
        for question, source, values, ids in [
            (count, "assets.json", [4], 4),
            ("and how many per terminal?", "assets.json", [2,2], 4),
            (ranking, "activity.json", [122]*4, 244),
            (retail, "activity.json", [1050], 62)]:
            turn = final_turn if question==ranking else docs[question][-1]
            self.assertEqual(turn["status"],"verified",stdout)
            evidence = turn["response"]["evidence"]
            # A Series may name a number "value"; a table may keep its source name.
            # Compare the observed facts, independent of the model's column labels.
            def matches(read):
                rows = read["rows"]
                if question == count and len(rows) == 4:
                    return (read["source"] == source and len(set(read["record_ids"])) == ids
                            and {r.get("member") for r in rows} == set(read["record_ids"]))
                return (read["source"] == source and len(set(read["record_ids"])) == ids
                        and len(rows) == len(values)
                        and all(any(v == expected for v in row.values()) for row, expected in zip(rows, values)))
            reads = [evidence, *evidence["supporting"]]
            matched = next((r for r in reads if matches(r)), None)
            self.assertIsNotNone(matched, [(r["source"], r["rows"]) for r in reads])
            if question == "and how many per terminal?":
                self.assertEqual({r["scope_name"] for r in matched["rows"]},{"North Terminal","South Terminal"})
            if question == ranking:
                self.assertEqual({r["member"] for r in matched["rows"]},
                                 {"harbor_north_c01","harbor_north_c02","harbor_south_c01","harbor_south_c02"})
