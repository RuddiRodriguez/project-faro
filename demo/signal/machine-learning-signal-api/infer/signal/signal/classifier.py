from faro_signal.quality.classifier import Classifier as DecisionClassifier
from faro_signal.quality.classifier_input import ClassifierInput as QualityInput
from faro_signal.classifier_input import ClassifierInput
from faro_signal.classifier_output import ClassifierOutput
from utils.openai_client.openai_client import OpenAiClient


class Classifier:
    def __init__(self, primary_llm_client: OpenAiClient):
        self.classifier = DecisionClassifier(primary_llm_client)

    def classify(self, classifier_input: ClassifierInput) -> ClassifierOutput:
        if not classifier_input.permitted_scopes:
            return ClassifierOutput(action="Unsupported")

        if classifier_input.unclear_references:
            return ClassifierOutput(action="Ask", missing_choice="Which is meant: " + " or ".join(classifier_input.unclear_references))


        classification = self.classifier.classify(
            QualityInput.model_validate(classifier_input, from_attributes=True)
        )
        if not classification.is_success:
            raise RuntimeError(classification.error_message)
        return classification.result
