from api_objects.faro.thread.input.thread_input import ThreadInput as ApiPredictorInput
from api_objects.faro.thread.output.thread_output import ThreadOutput as ApiPredictorOutput
from thread.predictor import Predictor
from thread.predictor_input import PredictorInput as LibPredictorInput, ConversationMessage as LibConversationMessage


class PredictEndpoint:
    def __init__(self, predictor: Predictor):
        self.predictor = predictor

    def handle(self, api_input: ApiPredictorInput) -> ApiPredictorOutput:
        predictor_input = LibPredictorInput(question=api_input.question,
                                            conversation=[LibConversationMessage(role=message.role, content=message.content)
                                                          for message in api_input.conversation])
        result = self.predictor.predict(predictor_input)
        return ApiPredictorOutput(unclear_references=result.unclear_references, question=result.question,
                                  used_ai=result.used_ai,
                                  model_name=result.model_name,
                                  token_usage=result.token_usage)
