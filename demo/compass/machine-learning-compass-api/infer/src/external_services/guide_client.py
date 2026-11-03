from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.guide.input.guide_input import GuideInput, Passage
from api_objects.faro.guide.output.guide_output import GuideOutput
from api_objects.faro.scout.output.scout_output import ScoutOutput


class GuideClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Guide"

    def generate_followup(self, search: ScoutOutput, missing_choice: str, language: str | None, unclear_references, user_messages, documents) -> GuideOutput:
        request = GuideInput(question_text=search.query, user_messages=user_messages, missing_choice=missing_choice, language=language,
                             passages=[Passage(title=m.title, text=m.text) for m in documents] if not unclear_references else [])
        return call(self.service_name, self.base_url, "/v1/followup", request, GuideOutput, timeout=100)
