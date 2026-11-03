from faro_signal.quality.classifier import Classifier
from faro_signal.quality.classifier_input import ClassifierInput
from faro_signal.predictor_input import PredictorInput
from faro_signal.predictor_output import PredictorOutput
from utils.openai_client.openai_client import OpenAiClient


class Predictor:
    def __init__(self, primary_llm_client: OpenAiClient):
        self.classifier = Classifier(primary_llm_client)

    def predict(self, predictor_input: PredictorInput) -> PredictorOutput:
        if not predictor_input.permitted_scopes:
            return PredictorOutput(action="Unsupported")

        if predictor_input.unclear_references:
            return PredictorOutput(action="Ask", missing_choice="Which is meant: " + " or ".join(predictor_input.unclear_references))


        classification = self.classifier.classify(
            ClassifierInput.model_validate(predictor_input, from_attributes=True)
        )
        if not classification.is_success:
            raise RuntimeError(classification.error_message)
        return classification.result
