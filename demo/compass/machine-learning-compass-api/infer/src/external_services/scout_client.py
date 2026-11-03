from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.library.output.library_output import LibraryOutput
from api_objects.faro.scout.input.scout_input import ScoutInput
from api_objects.faro.scout.output.scout_output import ScoutOutput


class ScoutClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Scout"

    def search_definitions(self, question: str, information: LibraryOutput) -> ScoutOutput:
        documents = {doc.document_id: doc for doc in information.documents}
        request = ScoutInput(company_id=information.company.company_id, query=question,
                             document_ids=list(documents), permitted_scope_ids=[s.scope_id for s in information.scopes])
        result = call(self.service_name, self.base_url, "/v1/search", request, ScoutOutput, timeout=15)
        for match in result.matches:
            document = documents.get(match.document_id)
            if (document is None or match.version != document.version or match.text != document.text
                    or match.source != document.source or match.title != document.title):
                raise ValueError("Scout returned a document outside the current approved information")
        return result
