import json
from pathlib import Path

from bridge.prompts.read_prompt import ReadDecision, ReadPrompt
from bridge.reader_output import ReaderOutput
from bridge.source import catalogue, execute, snapshot_id
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage


class Reader:
    def __init__(self, data_path: Path, llm_handler):
        self.data_path = data_path
        self.llm_handler = llm_handler

    def _build_conversation(self, request, sources, observations):
        conversation = Conversation(intelligence_level=IntelligenceLevel.LIGHT,
            system_message=SystemMessage(content=ReadPrompt.SYSTEM_MESSAGE))
        conversation.add_message(UserMessage(content=ReadPrompt.USER_MESSAGE.format(
            question=request.question, catalogue=json.dumps(sources, ensure_ascii=False),
            observations=json.dumps(observations, ensure_ascii=False), steps_remaining=6-len(observations))))
        return conversation

    def _parse_chat_prediction_output(self, prediction):
        if not prediction.is_success or not prediction.assistant_tools:
            raise ValueError("Bridge received no structured read.")
        return ReadDecision.model_validate(prediction.assistant_tools[0].parsed_arguments)

    def read(self, request):
        sources = catalogue(self.data_path, request)
        context = dict(company_id=request.company_id, question=request.question)
        reads, observations = [], []
        for step in range(6):
            prediction = self.llm_handler.predict(conversation=self._build_conversation(request, sources, observations),
                structured_output=ReadPrompt.STRUCTURED_OUTPUT, timeout=30, enable_auto_fix_json=False)
            try:
                decision = self._parse_chat_prediction_output(prediction)
            except ValueError:
                return ReaderOutput(**context, status="incomplete",
                                       reason="I could not finish reading the evidence. No result was verified.")
            if decision.action in ("clarify", "unavailable"):
                return ReaderOutput(**context, status="ask" if decision.action == "clarify" else "not_supported",
                                       reason=decision.reason or "The information available does not support an answer.")
            if decision.action == "answer":
                if not decision.findings or any(not f.evidence_ids or not set(f.evidence_ids).issubset(range(len(reads)+1))
                                                for f in decision.findings):
                    observations.append({"error":"Each finding needs an existing evidence ID."})
                    continue
                result = reads[0] if reads else ReaderOutput(**context,status="ready",source="catalogue",
                                                               data_version=sources["data_version"])
                return result.model_copy(update={"findings":decision.findings, "supporting":reads[1:],
                                                 "catalogue_version":snapshot_id(sources)})
            if decision.read is None:
                observations.append({"error":"No read supplied."})
                continue
            try:
                result = execute(self.data_path, request, decision.read)
            except (PermissionError, ValueError) as error:
                observations.append({"attempt":decision.read.model_dump(mode="json"),"error":str(error)})
                continue
            reads.append(result)
            observations.append({"id":len(reads), **result.model_dump(mode="json",
                include={"read","rows","period","source","unit"})})
        return ReaderOutput(**context,status="incomplete",reason="No supported answer within the read budget.")
