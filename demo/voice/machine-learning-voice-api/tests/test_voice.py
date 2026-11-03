import os
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
from bridge.source import execute
from api_objects.faro.bridge.output.bridge_output import Read
from bridge.reader_input import ReaderInput as RankingRequest
from shield.verifier import Verifier as Shield
from shield.verifier_input import VerifierInput as Check
from voice.generator import Generator, checked_lines
from voice.generator_input import GeneratorInput
from voice_api.infer import app


DATA = Path(__file__).resolve().parents[3] / "local_data/demo_dataset"


def verified_read(company, scopes, source, group, order):
    request = RankingRequest(question="Compare the members in October",company_id=company,permitted_scope_ids=scopes,definition_ids=[source])
    read = Read(source=source,scope_ids=scopes,group=group,member_ids=[],start="2026-10-01",end_exclusive="2026-11-01",
        expression=("(df.groupby('asset_id')['occupied_room_nights'].sum()/df.groupby('asset_id')['available_room_nights'].sum()*100)" if company=="meridian" else "df.groupby('asset_id')['downtime_hours'].sum()")+f".sort_values(ascending={order=='ASC'})")
    evidence = execute(DATA,request,read)
    handler = Mock()
    handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={"initial_analysis":"Supplied test evidence.", "reasoning":"Supported test decision.", "decision":"supported","reason":"Matches"})]
    return Shield(DATA,handler).verify(Check(**request.model_dump(), evidence=evidence))


def hotel_request():
    verified = verified_read("meridian", ["madrid","tokyo","mexico_city"], "meridian_measure", "hotel", "ASC")
    return GeneratorInput(question="¿Qué hotel tuvo la ocupación más baja en octubre?", language="es",
        measure="Occupancy", definition="Occupied room nights divided by available room nights, times 100.",
        definition_source="meridian/measure.md", verification=verified.model_dump())


def withheld(language):
    return GeneratorInput(question="Why is there no ranking?", language=language, names=["Tokyo Bay"], verification=dict(
        status="withheld", reason="Daily records are missing for Tokyo Bay."))


class VoiceTests(unittest.TestCase):
    def test_verified_answer_returns_documents_without_model_invented_links(self):
        from api_objects.faro.bridge.output.bridge_output import Finding
        request=hotel_request()
        facts=request.verification.facts
        facts.findings=[Finding(text="A checked answer.",evidence_ids=[1])]
        evidence=dict(document=dict(name="report.pdf",uri="file:///saved/report.pdf",version="v1"),
                      references=["report.pdf#page 1"])
        facts.source_evidence=[evidence, evidence]
        answer=Generator(Mock()).generate(request)
        self.assertEqual(len(answer.documents),1)
        self.assertEqual(answer.documents[0].uri,"file:///saved/report.pdf")
        self.assertEqual(answer.documents[0].references,["report.pdf#page 1"])
        request.verification.status="withheld"
        self.assertEqual(Generator(Mock()).generate(request.model_copy(update={"language":"en"})).documents,[])

    def test_withheld_without_ai(self):
        handler = Mock()
        answer = Generator(handler).generate(withheld("en"))
        self.assertEqual(answer.mode,"direct")
        self.assertEqual(answer.status,"withheld")
        self.assertIn("Tokyo Bay",answer.text)
        handler.predict.assert_not_called()

    def test_model_cannot_substitute_another_number_or_omit_a_member(self):
        request = hotel_request()
        template, _ = checked_lines(request)
        for bad in [template.replace("[[value_0]]","75%"), template.replace("[[name_2]]",""),template+" 18%"]:
            handler = Mock()
            handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={"initial_analysis":"Supplied test evidence.", "reasoning":"Supported test decision.", "text":bad})]
            answer = Generator(handler).generate(request)
            self.assertEqual(answer.mode,"fallback")
            self.assertIn("70%",answer.text)
            self.assertNotIn("75%",answer.text)
            self.assertIn("Mexico City Plaza",answer.text)
            self.assertIn("meridian/measure.md",answer.sources)

    def test_tie_survives_model_failure(self):
        verification = verified_read("harbor",["harbor_north"],"harbor_downtime_v1","crane","DESC")
        handler = Mock()
        handler.predict.side_effect = RuntimeError("unavailable")
        answer = Generator(handler).generate(GeneratorInput(question="Which cranes had the most downtime?",
            language="en", verification=verification.model_dump(), measure="Downtime"))
        self.assertEqual(answer.text.count("62 hours, tied at rank 1"), 2)
        self.assertIn("harbor_north_c01",answer.text)
        self.assertIn("harbor_north_c02",answer.text)

    def test_model_outage_returns_checked_ranking(self):
        handler = Mock()
        handler.predict.side_effect = RuntimeError("unavailable")
        answer = Generator(handler).generate(hotel_request())
        self.assertEqual(answer.mode,"fallback")
        self.assertIn("Tokyo Bay: 70%",answer.text)

    @unittest.skipUnless(os.getenv("FARO_RUN_LIVE_TESTS") == "1","Requires live model call")
    def test_live_spanish_ranking_and_withheld_reason(self):
        with TestClient(app) as client:
            for request in (hotel_request(),withheld("es")):
                response = client.post("/v1/answer", json=request.model_dump(mode="json"))
                self.assertEqual(response.status_code,200,response.text)
                answer = response.json()
                self.assertEqual(answer["mode"],"ai",answer)
                self.assertIn("Tokyo Bay",answer["text"])
                if answer["status"] == "verified":
                    self.assertIn("70%",answer["text"])
                    self.assertRegex(answer["text"].lower(),r"menor|menores|baja|bajo|ascendente")
                else:
                    self.assertNotIn("%",answer["text"])
                    self.assertRegex(answer["text"].lower(),r"faltan|falta|incomplet|no hay")
                print(answer["text"])
