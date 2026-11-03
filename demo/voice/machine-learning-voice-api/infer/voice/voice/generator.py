import re

from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage
from utils.openai_client.exceptions import OpenAiError
from utils.openai_client.outputs.predict_output import PredictOutput

from voice.generator_input import GeneratorInput
from voice.generator_output import GeneratorOutput
from voice.prompts.answer_prompt import AnswerPrompt, Wording


SLOT = re.compile(r"\[\[([a-z_0-9]+)\]\]")


def checked_lines(request):
    facts = request.verification.facts
    slots = {"period": facts.period, "measure": request.measure or facts.read.group, "source": facts.source}
    lines = ["[[measure]], [[period]] (source: [[source]]):"]
    for i, row in enumerate(facts.rows):
        unit = "" if facts.read.source == "register" else facts.unit
        number = str(row["value"]).removesuffix(".0")
        slots[f"value_{i}"] = number + (unit if unit == "%" or not unit else " " + unit)
        labels = [str(value) for key, value in row.items() if key != "value"]
        if labels:
            slots[f"name_{i}"] = ", ".join(labels)
            ordered = ".sort_values(" in facts.read.expression
            equal = [j for j, other in enumerate(facts.rows) if other["value"] == row["value"]]
            suffix = ""
            if ordered:
                slots[f"rank_{i}"] = str(equal[0] + 1)
                suffix = f", {'tied at rank' if len(equal) > 1 else 'rank'} [[rank_{i}]]"
            lines.append(f"[[name_{i}]]: [[value_{i}]]{suffix}.")
        else:
            lines.append(f"Total: [[value_{i}]].")
    return "\n".join(lines), slots


def used_documents(facts):
    documents = {}
    for observation in [facts, *facts.supporting]:
        for evidence in observation.source_evidence:
            document = evidence.get("document")
            if document:
                key = (document["uri"], document["version"])
                item = documents.setdefault(key, {**document, "references": []})
                item["references"] = list(dict.fromkeys([*item["references"], *evidence["references"]]))
    return list(documents.values())


class Generator:
    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler

    def _build_conversation(self, question, definition, template):
        conversation = Conversation(intelligence_level=IntelligenceLevel.YOLO,
            system_message=SystemMessage(content=AnswerPrompt.SYSTEM_MESSAGE))
        conversation.add_message(UserMessage(content=AnswerPrompt.USER_MESSAGE.format(question=question,
            definition=definition, source_lines=template)))
        return conversation

    def _parse_chat_prediction_output(self, prediction: PredictOutput):
        if not prediction.is_success or not prediction.assistant_tools:
            raise ValueError("Voice received no structured wording")
        return Wording.model_validate(prediction.assistant_tools[0].parsed_arguments).text

    def generate(self, request: GeneratorInput) -> GeneratorOutput:
        status = request.verification.status
        if status == "verified" and request.verification.facts.findings:
            facts = request.verification.facts
            sources = list(dict.fromkeys(obs.source for obs in [facts, *facts.supporting] if obs.source))
            return GeneratorOutput(status=status, text="\n".join([*(f.text for f in facts.findings), *([request.verification.reason] if request.verification.reason else [])]),
                                   sources=sources, documents=used_documents(facts), mode="direct")
        sources = []
        if status == "withheld":
            template = "I cannot verify this result. " + (request.verification.reason or "The records could not be verified.")
            return GeneratorOutput(status=status, text=template, sources=[], mode="direct")
        else:
            template, slots = checked_lines(request)
            sources = [request.verification.facts.source]
            if request.definition_source:
                sources.append(request.definition_source)
        try:
            prediction = self.llm_handler.predict(conversation=self._build_conversation(
                request.question if status == "verified" else "", request.definition if status == "verified" else None, template),
                structured_output=AnswerPrompt.STRUCTURED_OUTPUT, timeout=30, enable_auto_fix_json=False)
            text = self._parse_chat_prediction_output(prediction)
            if SLOT.findall(text) != SLOT.findall(template) or re.findall(r"\d+", SLOT.sub("", text)) != re.findall(r"\d+", SLOT.sub("", template)):
                raise ValueError("Answer changed the checked facts")
            mode = "ai"
        except (ValueError, RuntimeError, OpenAiError):
            text, mode = template, "fallback"
        return GeneratorOutput(status=status, text=SLOT.sub(lambda m: slots.get(m[1], m[0]), text), sources=sources,
                               definition=request.definition if status == "verified" else None, mode=mode,
                               documents=used_documents(request.verification.facts) if status == "verified" else [])
