from api_objects.faro.scout.input.scout_input import ScoutInput as ApiPredictorInput
from api_objects.faro.scout.output.scout_output import ScoutOutput as ApiPredictorOutput, SearchMatch
from utils.connector_client import sources
from scout.predictor import Predictor
from scout.predictor_input import PredictorInput as LibPredictorInput


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(company_id=api_input.company_id,
                                            query=api_input.query,
                                            document_ids=api_input.document_ids)
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(query=result.query, source_items=sources(api_input.company_id,api_input.permitted_scope_ids).items, matches=[
            SearchMatch(document_id=m.document_id, title=m.title, source=m.source, text=m.text,
                        version=m.version, file_reference=m.file_reference, score=m.score) for m in result.matches])
