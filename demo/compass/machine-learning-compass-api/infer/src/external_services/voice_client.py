from api_objects.faro.voice.input.voice_input import VoiceInput
from api_objects.faro.voice.output.voice_output import VoiceOutput
from compass_api.external_services.http_caller_with_exception_on_error import call


class VoiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def write_answer(self, question, language, verification, search) -> VoiceOutput:
        definition = None
        if verification.status == "verified" and verification.facts.read:
            definition = next((m for m in search.matches if m.document_id == verification.facts.read.source), None)
        request = VoiceInput(question=question, language=language, verification=verification, names=[],
                             measure=definition.title if definition else None,
                             definition=definition.text if definition else None,
                             definition_source=definition.source if definition else None)
        return call("Voice", self.base_url, "/v1/answer", request, VoiceOutput, timeout=100)
