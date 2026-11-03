from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.scout.input.scout_input import ScoutInput
from api_objects.faro.scout.output.scout_output import ScoutOutput


class ScoutClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def search_sources(self, question, access):
        request = ScoutInput(company_id=access.company_id, query=question,
                             permitted_scope_ids=access.permitted_scope_ids)
        return call("Scout", self.base_url, "/v1/search", request, ScoutOutput, timeout=100)
