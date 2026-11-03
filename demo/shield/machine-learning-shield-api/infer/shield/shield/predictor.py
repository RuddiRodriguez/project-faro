import json
from pathlib import Path

from shield.predictor_files.review_prompt import FindingsReview, Review, ReviewPrompt
from api_objects.faro.bridge.output.bridge_output import Observation
from bridge.source import catalogue, execute, snapshot_id
from shield.predictor_output import PredictorOutput
from utils.openai_client.exceptions import OpenAiRecoverableError
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage


class Predictor:
    def __init__(self, data_path: Path, llm_handler):
        self.data_path, self.llm_handler = data_path, llm_handler

    def predict(self, request):
        try:
            return self._verify(request)
        except OpenAiRecoverableError:
            return PredictorOutput(status="withheld", reason="The verification model was unavailable after three attempts.")

    def _verify(self, request):
        evidence = request.evidence
        if evidence.status != "ready":
            return PredictorOutput(status="withheld", reason=evidence.reason or "Bridge returned no verified records.")
        cat = catalogue(self.data_path, request)
        if evidence.company_id != request.company_id or evidence.question != request.question:
            return PredictorOutput(status="withheld",reason="The evidence belongs to another request.")
        if evidence.findings and evidence.catalogue_version != snapshot_id(cat):
            return PredictorOutput(status="withheld",reason="The permitted catalogue changed.")
        reads = ([evidence] if evidence.read else []) + list(evidence.supporting)
        if not reads and not (evidence.source=="catalogue" and evidence.findings):
            return PredictorOutput(status="withheld",reason="No supporting evidence.")
        observations = []
        for index, obs in enumerate(reads,1):
            try:
                replay = execute(self.data_path,request,obs.read)
            except (ValueError,PermissionError) as error:
                return PredictorOutput(status="withheld",reason=str(error))
            if replay.model_dump(include=set(Observation.model_fields)) != obs.model_dump(include=set(Observation.model_fields)):
                return PredictorOutput(status="withheld",reason="The result does not match the permitted source records.")
            observations.append({"id":index,"selection":obs.read.model_dump(mode="json"),
                "includes_all_permitted_locations": not obs.read.scope_ids or set(obs.read.scope_ids)==set(cat["scopes"]),
                "original_source_rows":obs.source_evidence, "actual_dates":obs.period, "result":obs.rows, "unit":obs.unit})
        if any(not f.evidence_ids or not set(f.evidence_ids).issubset(range(len(reads)+1)) for f in evidence.findings):
            return PredictorOutput(status="withheld",reason="Finding cites unavailable evidence.")
        def check(findings):
            conversation = Conversation(intelligence_level=IntelligenceLevel.LIGHT,
                system_message=SystemMessage(content=ReviewPrompt.SYSTEM_MESSAGE))
            conversation.add_message(UserMessage(content=json.dumps(dict(question=request.question, catalogue=cat,
                observations=observations, findings=[f.model_dump() for f in findings]))))
            prediction = self.llm_handler.predict(conversation=conversation,
                structured_output=ReviewPrompt.FINDINGS_OUTPUT if findings else ReviewPrompt.STRUCTURED_OUTPUT,
                timeout=30, enable_auto_fix_json=False)
            if not prediction.is_success or not prediction.assistant_tools:
                return None
            return prediction.assistant_tools[0].parsed_arguments

        parsed = check(evidence.findings)
        if parsed is None:
            return PredictorOutput(status="withheld",reason="Could not verify the findings.")
        if evidence.findings:
            review = FindingsReview.model_validate(parsed)
            keep = set(review.supported_finding_numbers)
            if not keep.issubset(range(1,len(evidence.findings)+1)):
                return PredictorOutput(status="withheld",reason="Review refers to an unknown finding.")
            findings = [f for i,f in enumerate(evidence.findings,1) if i in keep]
            narrower = [f for f in review.narrower_findings if f.evidence_ids and
                        set(f.evidence_ids).issubset(range(len(reads)+1))]
            if narrower:
                second = check(narrower)
                if second:
                    passed = FindingsReview.model_validate(second).supported_finding_numbers
                    findings.extend(f for i,f in enumerate(narrower,1) if i in passed)
            if not findings:
                return PredictorOutput(status="withheld",reason=review.reason)
            return PredictorOutput(status="verified",facts=evidence.model_copy(update={"findings":findings}),
                reason="Only supported findings are shown." if len(keep)<len(evidence.findings) else None)
        review = Review.model_validate(parsed)
        if review.decision == "withhold":
            return PredictorOutput(status="withheld", reason=review.reason)
        return PredictorOutput(status="verified", facts=evidence)
