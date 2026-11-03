import json
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path

from shield.prompts.review_prompt import FindingsReview, Review, ReviewPrompt
from api_objects.faro.bridge.output.bridge_output import Observation
from bridge.source import catalogue, execute, snapshot_id
from shield.verifier_output import VerifierOutput
from utils.openai_client.exceptions import OpenAiRecoverableError
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage


class Verifier:
    def __init__(self, data_path: Path, llm_handler):
        self.data_path, self.llm_handler = data_path, llm_handler

    def verify(self, request):
        try:
            return self._verify(request)
        except OpenAiRecoverableError:
            return VerifierOutput(status="withheld", reason="The verification model was unavailable after three attempts.")

    def _verify(self, request):
        evidence = request.evidence
        if evidence.status != "ready":
            return VerifierOutput(status="withheld", reason=evidence.reason or "Bridge returned no verified records.")
        cat = catalogue(self.data_path, request)
        if evidence.company_id != request.company_id or evidence.question != request.question:
            return VerifierOutput(status="withheld",reason="The evidence belongs to another request.")
        if evidence.findings and evidence.catalogue_version != snapshot_id(cat):
            return VerifierOutput(status="withheld",reason="The permitted catalogue changed.")
        reads = ([evidence] if evidence.read else []) + list(evidence.supporting)
        if not reads and not (evidence.source=="catalogue" and evidence.findings):
            return VerifierOutput(status="withheld",reason="No supporting evidence.")
        observations = []
        with ThreadPoolExecutor() as pool:
            replays = [pool.submit(copy_context().run, execute, self.data_path, request, obs.read) for obs in reads]
            for index, (obs, replay_task) in enumerate(zip(reads, replays),1):
                try:
                    replay = replay_task.result()
                except (ValueError,PermissionError) as error:
                    return VerifierOutput(status="withheld",reason=str(error))
                if replay.model_dump(include=set(Observation.model_fields)) != obs.model_dump(include=set(Observation.model_fields)):
                    return VerifierOutput(status="withheld",reason="The result does not match the permitted source records.")
                observations.append({"id":index,"selection":obs.read.model_dump(mode="json"),
                    "includes_all_permitted_locations": not obs.read.scope_ids or set(obs.read.scope_ids)==set(cat["scopes"]),
                    "link_check":replay.link_check, "original_source_rows":obs.source_evidence, "actual_dates":obs.period, "result":obs.rows, "unit":obs.unit})
        if any(not f.evidence_ids or not set(f.evidence_ids).issubset(range(len(reads)+1)) for f in evidence.findings):
            return VerifierOutput(status="withheld",reason="Finding cites unavailable evidence.")
        def check(findings):
            conversation = Conversation(intelligence_level=IntelligenceLevel.LIGHT,
                system_message=SystemMessage(content=ReviewPrompt.SYSTEM_MESSAGE))
            conversation.add_message(UserMessage(content=ReviewPrompt.USER_MESSAGE.format(question=request.question, catalogue=json.dumps(cat),
                observations=json.dumps(observations), findings=json.dumps([f.model_dump() for f in findings]))))
            prediction = self.llm_handler.predict(conversation=conversation,
                structured_output=ReviewPrompt.FINDINGS_OUTPUT if findings else ReviewPrompt.STRUCTURED_OUTPUT,
                timeout=30, enable_auto_fix_json=False)
            if not prediction.is_success or not prediction.assistant_tools:
                return None
            return prediction.assistant_tools[0].parsed_arguments

        parsed = check(evidence.findings)
        if parsed is None:
            return VerifierOutput(status="withheld",reason="Could not verify the findings.")
        if evidence.findings:
            review = FindingsReview.model_validate(parsed)
            keep = set(review.supported_finding_numbers)
            if not keep.issubset(range(1,len(evidence.findings)+1)):
                return VerifierOutput(status="withheld",reason="Review refers to an unknown finding.")
            findings = [f for i,f in enumerate(evidence.findings,1) if i in keep]
            if not findings:
                return VerifierOutput(status="withheld",reason=review.reason)
            return VerifierOutput(status="verified",facts=evidence.model_copy(update={"findings":findings}),
                reason="Only supported findings are shown." if len(keep)<len(evidence.findings) else None)
        review = Review.model_validate(parsed)
        if review.decision == "withhold":
            return VerifierOutput(status="withheld", reason=review.reason)
        return VerifierOutput(status="verified", facts=evidence)
