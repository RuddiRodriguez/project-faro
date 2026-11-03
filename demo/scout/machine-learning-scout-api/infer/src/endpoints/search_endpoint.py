from api_objects.faro.scout.input.scout_input import ScoutInput as ApiSearcherInput
from api_objects.faro.scout.output.scout_output import ScoutOutput as ApiSearcherOutput, SearchMatch
from utils.connector_client import sources
from scout.searcher import Searcher
from scout.searcher_input import SearcherInput as LibSearcherInput


class SearcherEndpoint:
    def __init__(self, searcher: Searcher):
        self.searcher = searcher

    def handle(self, api_input: ApiSearcherInput) -> ApiSearcherOutput:
        searcher_input = LibSearcherInput(company_id=api_input.company_id,
                                            query=api_input.query,
                                            permitted_scope_ids=api_input.permitted_scope_ids)
        result = self.searcher.search(searcher_input)
        return ApiSearcherOutput(query=result.query, source_items=sources(api_input.company_id,api_input.permitted_scope_ids).items, matches=[
            SearchMatch(document_id=m.document_id, title=m.title, source=m.source, text=m.text,
                        version=m.version, file_reference=m.file_reference, score=m.score) for m in result.matches])
