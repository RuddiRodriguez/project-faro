from api_objects.faro.compass.input.compass_input import CompassInput as ApiPredictorInput
from api_objects.faro.compass.output.compass_output import CompassOutput as ApiPredictorOutput
from compass.predictor import Predictor
from compass.predictor_input import PredictorInput as LibPredictorInput, ConversationMessage as LibConversationMessage


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(conversation_id=api_input.conversation_id, previous_answer_id=api_input.previous_answer_id, user_id=api_input.user_id,
                                            question=api_input.question, language=api_input.language,
                                            conversation=[LibConversationMessage(role=message.role, content=message.content)
                                                          for message in api_input.conversation])
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(conversation_id=result.conversation_id, turn_id=result.turn_id, question=result.question,
                                  access=result.access,
                                  company_information=result.company_information,
                                  rewrite=result.rewrite,
                                  search=result.search,
                                  decision=result.decision, followup=result.followup, evidence=result.evidence, verification=result.verification, answer=result.answer)
