from api_objects.faro.signal.input.signal_input import SignalInput as ApiClassifierInput
from api_objects.faro.signal.output.signal_output import SignalOutput as ApiClassifierOutput
from faro_signal.classifier import Classifier
from faro_signal.classifier_input import ClassifierInput as LibClassifierInput, Passage


class ClassifierEndpoint:
    def __init__(self, classifier: Classifier):
        self.classifier = classifier

    def handle(self, api_input: ApiClassifierInput) -> ApiClassifierOutput:
        classifier_input = LibClassifierInput(
            unclear_references=api_input.unclear_references,
            question=api_input.question,
            matches=[Passage(title=m.title, text=m.text, source=m.source) for m in api_input.matches],
            permitted_scopes=api_input.permitted_scopes,
        )
        result = self.classifier.classify(classifier_input)
        return ApiClassifierOutput(initial_analysis=result.initial_analysis, reasoning=result.reasoning, action=result.action, missing_choice=result.missing_choice)
