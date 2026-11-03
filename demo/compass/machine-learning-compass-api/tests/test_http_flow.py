import os
from pathlib import Path
from tempfile import TemporaryDirectory
import socket
import subprocess
import sys
import time
import unittest

import httpx


def free_port():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        return connection.getsockname()[1]


@unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Starts all APIs and calls the configured models")
class CompassHttpTests(unittest.TestCase):
    @classmethod
    def start_server(cls, module, **settings):
        port = free_port()
        url = f'http://127.0.0.1:{port}'
        process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', f'{module}:app',
             '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
            env={**os.environ, "FARO_COLLECTION_PATH": str(cls.collection_path), **settings}, stdout=subprocess.DEVNULL)

        def stop():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        cls.addClassCleanup(stop)
        with httpx.Client(timeout=1) as client:
            deadline = time.monotonic() + (240 if module == "scout_api.infer" else 60)
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f'{module} failed to start')
                try:
                    if client.get(f'{url}/openapi.json').status_code == 200:
                        return url
                except httpx.RequestError:
                    pass
                time.sleep(0.05)
        raise RuntimeError(f'{module} did not become ready')

    @classmethod
    def setUpClass(cls):
        folder = TemporaryDirectory()
        cls.addClassCleanup(folder.cleanup)
        cls.collection_path = Path(os.getenv('FARO_TEST_COLLECTION_PATH',folder.name))
        cls.gate_url = cls.start_server('gate_api.infer')
        cls.library_url = cls.start_server('library_api.infer')
        cls.thread_url = cls.start_server('thread_api.infer')
        cls.scout_url = cls.start_server("scout_api.infer")
        cls.voice_url = cls.start_server("voice_api.infer")
        cls.shield_url = cls.start_server("shield_api.infer")
        cls.bridge_url = cls.start_server("bridge_api.infer")
        cls.guide_url = cls.start_server("guide_api.infer")
        cls.signal_url = cls.start_server("signal_api.infer")
        cls.compass_url = cls.start_server('compass_api.infer',
                                          FARO_GATE_URL=cls.gate_url,
                                          FARO_LIBRARY_URL=cls.library_url,
                                          FARO_THREAD_URL=cls.thread_url, FARO_SCOUT_URL=cls.scout_url, FARO_SIGNAL_URL=cls.signal_url, FARO_GUIDE_URL=cls.guide_url, FARO_BRIDGE_URL=cls.bridge_url, FARO_SHIELD_URL=cls.shield_url, FARO_VOICE_URL=cls.voice_url)
        cls.unavailable_url = cls.start_server('compass_api.infer',
                                              FARO_GATE_URL=cls.gate_url,
                                              FARO_LIBRARY_URL=f'http://127.0.0.1:{free_port()}',
                                              FARO_THREAD_URL=cls.thread_url, FARO_SCOUT_URL=cls.scout_url, FARO_SIGNAL_URL=cls.signal_url, FARO_GUIDE_URL=cls.guide_url, FARO_BRIDGE_URL=cls.bridge_url, FARO_SHIELD_URL=cls.shield_url, FARO_VOICE_URL=cls.voice_url)
        cls.unavailable_thread_url = cls.start_server('compass_api.infer',
                                                     FARO_GATE_URL=cls.gate_url,
                                                     FARO_LIBRARY_URL=cls.library_url,
                                                     FARO_THREAD_URL=f'http://127.0.0.1:{free_port()}')

        cls.unavailable_scout_url = cls.start_server("compass_api.infer",
            FARO_GATE_URL=cls.gate_url, FARO_LIBRARY_URL=cls.library_url,
            FARO_THREAD_URL=cls.thread_url, FARO_SCOUT_URL=f"http://127.0.0.1:{free_port()}")

        cls.unavailable_signal_url = cls.start_server("compass_api.infer", FARO_GATE_URL=cls.gate_url,
            FARO_LIBRARY_URL=cls.library_url, FARO_THREAD_URL=cls.thread_url, FARO_SCOUT_URL=cls.scout_url,
            FARO_SIGNAL_URL=f"http://127.0.0.1:{free_port()}")

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_maria_answers_guides_actual_question(self):
        first = "Which cranes performed badly at North Terminal last month?"
        response = self.ask("maria", question=first)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["decision"], {"action": "Ask", "missing_choice": "performance indicator"})
        followup = result["followup"]["followup_text"]
        self.assertTrue(followup.strip().endswith("?"), followup)
        self.assertRegex(followup.lower(), r"\b(which|what|how|would|do|are|should)\b")
        self.assertEqual(followup.count("?"), 1, followup)
        response = self.ask("maria", question="Downtime, highest first.", conversation=[
            {"role": "user", "content": first}, {"role": "assistant", "content": followup}])
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["decision"]["action"], "Continue", (result["rewrite"],result["decision"],result["followup"]))
        self.assertEqual(result["evidence"]["status"], "ready", (result["rewrite"]["question"], result["evidence"]))
        self.assertEqual([t["value"] for t in result["evidence"]["rows"]], [62, 62])
        self.assertIsNone(result["followup"])
        self.assertIn("62", result["answer"]["text"])
        self.assertIn("harbor_north_c01", result["answer"]["text"])
        self.assertIn("harbor_north_c02", result["answer"]["text"])
        for term in ["downtime", "north terminal", "last month"]:
            self.assertIn(term, result["rewrite"]["question"].lower())
        print("Guide:", followup, "Reply ->", result["rewrite"]["question"], "-> Continue")

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_retail_followup(self):
        history = [{"role": "user", "content": "I'm comparing the East and West stores."}]
        question = "Which ones did worst in October?"
        first = self.ask("sam", question=question, conversation=history)
        self.assertEqual(first.status_code, 200, first.text)
        first = first.json()
        self.assertIn("store", first["rewrite"]["question"].lower())
        self.assertEqual(first["decision"]["action"], "Ask", first)
        history.extend([{"role":"user","content":question},{"role":"assistant","content":first["followup"]["followup_text"]}])
        result = self.ask("sam", question="Highest return rate.", conversation=history)
        self.assertEqual(result.status_code, 200, result.text)
        result = result.json()
        self.assertEqual(result["verification"]["status"], "verified", result)
        self.assertEqual([(r["member"],r["value"]) for r in result["evidence"]["rows"]], [("West",10),("East",2)])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_ambiguous_reference(self):
        result = self.ask("sam", question="Which ones did worst in October?",
            conversation=[{"role":"user","content":"I am comparing stores and products."}]).json()
        self.assertEqual(result["decision"]["action"], "Ask", result)
        self.assertIsNone(result["evidence"])
        self.assertRegex(result["followup"]["followup_text"].lower(), "store")
        self.assertRegex(result["followup"]["followup_text"].lower(), "product")

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_unrepresented_filter(self):
        result = self.ask("maria", question="Rank North Terminal cranes by highest downtime last month on night shifts only.").json()
        self.assertIsNone(result["evidence"])
        self.assertNotEqual(result["decision"]["action"], "Continue")

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_hospital_and_hotel(self):
        for user, question, expected in [
            ("hospital_ops", "Rank all my hospitals by highest average outpatient waiting time in October 2026.",
             [("Hillview Hospital",45),("Riverside Hospital",30)]),
            ("hotel_hq", "Rank all my hotels worldwide by lowest occupancy rate in October 2026.",
             [("Tokyo Bay",70),("Madrid Central",80),("Mexico City Plaza",90)]),
            ("madrid_manager", "Show the October 2026 occupancy rate for Madrid Central, highest first.",
             [("Madrid Central",80)])]:
            with self.subTest(user=user):
                response = self.ask(user, question=question)
                self.assertEqual(response.status_code, 200,response.text)
                result = response.json()
                self.assertEqual(result["decision"]["action"],"Continue", (result["decision"],result["rewrite"]))
                self.assertEqual(result["verification"]["status"],"verified",result["verification"])
                self.assertEqual(result["answer"]["status"], "verified")
                self.assertIn(expected[0][0], result["answer"]["text"])
                self.assertEqual([(r["member"],r["value"]) for r in result["evidence"]["rows"]], expected)

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_manager_cannot_read_another_hotel(self):
        response = self.ask("madrid_manager",question="Show the October 2026 occupancy rate for Tokyo Bay, highest first.")
        self.assertEqual(response.status_code,200,response.text)
        self.assertIsNone(response.json()["evidence"],response.json()["decision"])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_voice_withheld_through_compass(self):
        response = self.ask("hotel_hq", question="Rank all my hotels by lowest occupancy in September 2026.", language="en")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["verification"]["status"], "withheld", result)
        self.assertIsNone(result["evidence"])
        self.assertEqual(result["answer"]["mode"], "direct")
        self.assertIn(result["verification"]["reason"], result["answer"]["text"])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires live model calls")
    def test_data_collection_multiple_turns_and_reuse(self):
        first = "Which cranes performed badly at North Terminal last month?"
        initial = self.ask("maria", question=first)
        self.assertEqual(initial.status_code,200,initial.text)
        start = initial.json()
        self.assertEqual(start["decision"]["action"], "Ask", start)
        cid = start["conversation_id"]
        reply = self.ask("maria", conversation_id=cid, question="Downtime, highest first.")
        self.assertEqual(reply.status_code,200,reply.text)
        self.assertEqual(reply.json()["verification"]["status"],"verified")
        from compass.data_collection import DataCollection
        store = DataCollection(self.collection_path)
        doc = store.read_conversation("harbor",cid)
        self.assertEqual(doc["original_question"],first)
        self.assertEqual([t["status"] for t in doc["turns"]],["Ask","verified"])
        self.assertEqual([m["role"] for m in doc["messages"]],["user","assistant","user","assistant"])
        self.assertEqual(doc["turns"][1]["response"]["answer"],reply.json()["answer"])
        self.assertEqual(self.ask("luis",conversation_id=cid,question="Show me more").status_code,403)
        q = "Rank all my hospitals by highest average outpatient waiting time in October 2026."
        for _ in range(2):
            result = self.ask("hospital_ops",question=q)
            self.assertEqual(result.status_code,200,result.text)
            self.assertEqual(result.json()["verification"]["status"],"verified")
        cid = result.json()["conversation_id"]
        turn = store.read_conversation("cedar",cid)["turns"][0]
        events = {e["service"]:e["result_source"] for e in turn["cache"]}
        for service in ("Signal","Bridge"):
            self.assertEqual(events[service],"cache",events)
        print("Repeat hospital question:", events)

    def test_signal_outage_is_not_unsupported(self):
        self.assertEqual(self.ask("maria", self.unavailable_signal_url).status_code, 503)

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions calls")
    def test_maria_three_decisions(self):
        for question, action, missing in [
            ("Which cranes at North Terminal had the most downtime last month?", "Continue", None),
            ("Which cranes performed badly at North Terminal last month?", "Ask", "performance indicator"),
            ("Show payroll for crane operators at North Terminal.", "Unsupported", None),
        ]:
            with self.subTest(action=action):
                response = self.ask("maria", question=question)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["decision"], {"action": action, "missing_choice": missing})
                self.assertEqual(response.json()["followup"] is not None, action == "Ask")
                evidence = response.json()["evidence"]
                if action == "Continue":
                    self.assertEqual(response.json()["verification"]["status"], "verified")
                    self.assertEqual(evidence["status"], "ready", evidence)
                    self.assertEqual((evidence["read"]["start"], evidence["read"]["end_exclusive"]), ("2026-10-01", "2026-11-01"))
                    self.assertEqual([x["value"] for x in evidence["rows"]], [62,62])
                    self.assertEqual(len(evidence["record_ids"]), 62)
                else:
                    self.assertIsNone(response.json()["verification"])
                    self.assertIsNone(evidence)
                print("Signal via Compass:", question, "=>", response.json()["decision"])

    def test_unavailable_scout_is_not_an_empty_search(self):
        self.assertEqual(self.ask("ana", self.unavailable_scout_url).status_code, 503)

    def test_no_permitted_documents_returns_no_matches(self):
        response = self.ask("noah")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["search"]["matches"], [])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions call")
    def test_search_for_permitted_definition(self):
        result = self.ask("ana", question="How many container moves per working hour?").json()
        match = result["search"]["matches"][0]
        self.assertEqual(match["document_id"], "harbor_moves_per_hour_v1")
        self.assertIn("operating hours", match["text"])

    def test_unrelated_topic_has_no_matches_in_either_language(self):
        for question in ("Which hotels in Barcelona had the lowest occupancy rate last quarter?",
                         "¿Qué hoteles de Barcelona tuvieron la ocupación más baja el trimestre pasado?"):
            with self.subTest(question=question):
                response = self.ask("maria", question=question)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["search"]["matches"], [])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions call")
    def test_maria_finds_same_definition_in_english_and_spanish(self):
        for question in ("How many container moves per working hour?",
                         "¿Cuántos movimientos hace una grúa por hora de trabajo?"):
            with self.subTest(question=question):
                response = self.ask("maria", question=question)
                self.assertEqual(response.status_code, 200, response.text)
                result = response.json()
                self.assertFalse(result["rewrite"]["used_ai"])
                self.assertEqual(result["search"]["query"], question)
                match = result["search"]["matches"][0]
                self.assertEqual(match["document_id"], "harbor_moves_per_hour_v1")
                print("Maria:", question, "=>", match["title"], round(match["score"], 4))

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid OpenAI call")
    def test_maria_spanish_followup(self):
        response = self.ask("maria", question="En la terminal norte.", conversation=[
            {"role": "user", "content": "¿Cuántos movimientos por hora de trabajo realizaron las grúas el mes pasado?"},
            {"role": "assistant", "content": "¿En qué terminal?"}])
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertTrue(result["rewrite"]["used_ai"])
        self.assertEqual(result["search"]["query"], result["rewrite"]["question"])
        self.assertEqual(result["search"]["matches"][0]["document_id"], "harbor_moves_per_hour_v1")
        print("Spanish follow-up:", result["search"]["query"])

    def ask(self, user_id, url=None, **extra):
        return httpx.post(f'{url or self.compass_url}/v1/questions', json={
            'user_id': user_id,
            'question': 'Which cranes performed badly last month?', **extra}, timeout=50)

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions call")
    def test_ana_question_and_north_only_information(self):
        response = self.ask('ana')
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['question'], 'Which cranes performed badly last month?')
        self.assertEqual(result['rewrite']['question'], result['question'])
        self.assertFalse(result['rewrite']['used_ai'])
        self.assertEqual(result['access']['user_id'], 'ana')
        information = result['company_information']
        self.assertEqual(information['company']['company_id'], 'harbor')
        self.assertEqual([item['scope_id'] for item in information['scopes']], ['harbor_north'])
        self.assertEqual(len(information['documents']), 4)
        self.assertNotIn('harbor_south', response.text)
        self.assertNotIn('pacific', response.text)

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions call")
    def test_request_cannot_replace_saved_permissions(self):
        response = self.ask('ana', company_id='pacific', permitted_scope_ids=['pacific_north'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['access']['company_id'], 'harbor')
        self.assertEqual(response.json()['access']['permitted_scope_ids'], ['harbor_north'])

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1", "Requires paid Decisions call")
    def test_other_company(self):
        response = self.ask('maya')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['company_information']['company']['company_id'], 'pacific')
        self.assertNotIn('harbor', response.text)

    def test_denied_user_stops_before_unavailable_library(self):
        for user_id in ['missing', 'former_user']:
            with self.subTest(user_id=user_id):
                self.assertEqual(self.ask(user_id, self.unavailable_url).status_code, 403)

    def test_unavailable_library_returns_failure_not_partial_result(self):
        response = self.ask('ana', self.unavailable_url)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('company_information', response.json())

    def test_missing_question(self):
        response = httpx.post(f'{self.compass_url}/v1/questions', json={'user_id': 'ana'})
        self.assertEqual(response.status_code, 422)

    def test_unavailable_thread_returns_failure_not_partial_result(self):
        response = self.ask('ana', self.unavailable_thread_url, question='October', conversation=[{'role':'user','content':'How much downtime?'},{'role':'assistant','content':'Which period?'}])
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('rewrite', response.json())

    def test_denied_user_stops_before_unavailable_thread(self):
        response = self.ask('former_user', self.unavailable_thread_url,
                            question='North Terminal.', conversation=[
                                {'role': 'user', 'content': 'Which cranes performed badly last month?'},
                                {'role': 'assistant', 'content': 'Which terminal?'}])
        self.assertEqual(response.status_code, 403)

    @unittest.skipUnless(os.getenv('FARO_RUN_LIVE_TESTS') == '1', 'Requires paid OpenAI call')
    def test_live_followup_through_all_six_apis(self):
        response = self.ask('ana', question='North Terminal.', conversation=[
            {'role': 'user', 'content': 'Which cranes performed badly last month?'},
            {'role': 'assistant', 'content': 'Which terminal?'}])
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["search"]["query"], result["rewrite"]["question"])
        self.assertTrue(result["search"]["matches"])
        rewritten = result['rewrite']['question'].lower()
        for phrase in ['cranes', 'badly', 'north terminal', 'last month']:
            self.assertIn(phrase, rewritten)
        self.assertEqual(result['question'], 'North Terminal.')
        self.assertTrue(result['rewrite']['used_ai'])
        self.assertGreater(result['rewrite']['token_usage']['prompt_tokens'], 0)
        self.assertNotIn('harbor_south', response.text)
        print('Live Compass rewrite:', result['rewrite']['question'])

    @unittest.skipUnless(os.getenv('FARO_RUN_LIVE_TESTS') == '1', 'Requires paid OpenAI call')
    def test_live_general_rewrite_does_not_change_company_permissions(self):
        response = self.ask('ana', question='Occupancy rate, lowest first.', conversation=[
            {'role': 'user', 'content': 'Which hotels performed poorly last quarter?'},
            {'role': 'assistant', 'content': 'Which city?'},
            {'role': 'user', 'content': 'Barcelona.'},
            {'role': 'assistant', 'content': 'Which performance indicator and comparison?'}])
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        for phrase in ['hotels', 'barcelona', 'occupancy', 'last quarter']:
            self.assertIn(phrase, result['rewrite']['question'].lower())
        self.assertEqual(result['access']['company_id'], 'harbor')
        self.assertEqual(result['access']['permitted_scope_ids'], ['harbor_north'])
        print('Live Compass industry change:', result['rewrite']['question'])


if __name__ == '__main__':
    unittest.main()
