from api_objects.faro.guide.input.guide_input import GuideInput as ApiPredictorInput
from api_objects.faro.guide.output.guide_output import GuideOutput as ApiPredictorOutput
from guide.predictor import Predictor
from guide.predictor_input import PredictorInput as LibPredictorInput, Definition


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(question_text=api_input.question_text, user_messages=api_input.user_messages,
            missing_choice=api_input.missing_choice, language=api_input.language,
            definitions=[Definition(title=d.title, text=d.text) for d in api_input.definitions])
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(followup_text=result.followup_text, proposed_changes=result.proposed_changes)
