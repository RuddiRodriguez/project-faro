import json
from time import perf_counter

from faro_signal.common_tools.custom_exceptions import ConversationError, JsonFormatError
from faro_signal.common_tools.error_code import ErrorCode
from faro_signal.common_tools.log_messages import ErrorMessages
from faro_signal.common_tools.logger_metadata import LoggerMetadata
from faro_signal.common_tools.predictor_logger import PredictorLogger
from faro_signal.prompts.decisions_prompt import DecisionsPrompt
from faro_signal.prompts.decisions_rules import DecisionsRules
from faro_signal.quality.classifier_input import ClassifierInput
from faro_signal.quality.classifier_output import ClassifierOutput
from faro_signal.classifier_output import ClassifierOutput as DecisionOutput
from utils.llms.llm_handler import LLMHandler
from utils.openai_client.conversation.decisions_conversation import DecisionsConversation
from utils.openai_client.exceptions import OpenAIGeneralError, OpenAiRecoverableError, OpenAiUnRecoverableError
from utils.openai_client.openai_client import OpenAiClient
from utils.openai_client.outputs.predict_output import PredictOutput

class Classifier:
    def __init__(self, primary_llm_client: OpenAiClient):
        self.llm_handler = LLMHandler(llm_client=primary_llm_client)

    def _build_conversation(self, classifier_input: ClassifierInput) -> DecisionsConversation:
        try:
            conversation = DecisionsConversation(
                llm_model_name=DecisionsPrompt.MODEL_NAME,
                input_text=DecisionsPrompt.INPUT_MESSAGE.format(
                    connected_sources=json.dumps(classifier_input.connected_sources),
                    question=json.dumps(classifier_input.question, ensure_ascii=False),
                    supported_tasks=json.dumps(classifier_input.supported_tasks, ensure_ascii=False),
                    groups=json.dumps(classifier_input.groups, ensure_ascii=False),
                    permitted_scopes=json.dumps(classifier_input.permitted_scopes, ensure_ascii=False),
                    matches=json.dumps([m.model_dump(include={"title", "text", "source"})
                                        for m in classifier_input.matches], ensure_ascii=False),
                ),
            )
            conversation.add_choice_question(
                name="next_action",
                instructions=DecisionsPrompt.NEXT_ACTION_INSTRUCTIONS,
                choices=[{"value": value, "description": description}
                         for value, description in DecisionsRules.CHOICES.items()],
            )
            conversation.add_choice_question(name="initial_analysis",
                instructions=DecisionsPrompt.INITIAL_ANALYSIS_INSTRUCTIONS, choices=[
                    {"value":"Company-data request", "description":"The question concerns permitted company information."},
                    {"value":"Unresolved user choice", "description":"A material choice remains for the user to make."},
                    {"value":"Unrelated request", "description":"The request is not about company data."}])
            conversation.add_choice_question(name="reasoning",
                instructions=DecisionsPrompt.REASONING_INSTRUCTIONS, choices=[
                    {"value":"Investigate the permitted evidence", "description":"Bridge can examine available sources before answering."},
                    {"value":"Clarify the user's intended meaning", "description":"Proceeding would require choosing on the user's behalf."},
                    {"value":"Outside the data-question service", "description":"The request asks for unrelated conversation."}])
            return conversation
        except Exception as error:
            raise ConversationError(ErrorMessages.ERROR_BUILDING_CONVERSATION.format(error)) from error

    def _parse_prediction_output(self, prediction: PredictOutput,
                                 classifier_input: ClassifierInput) -> DecisionOutput:
        try:
            if not prediction.is_success:
                raise JsonFormatError("Decisions returned missing or duplicate answers")
            if prediction.assistant_message is None:
                raise JsonFormatError("Decisions returned no assistant message")
            answers = json.loads(prediction.assistant_message.content)
            if not isinstance(answers, list) or not all(isinstance(answer, dict) for answer in answers):
                raise JsonFormatError("Decisions answers must be a list of objects")
            by_name = {answer["name"]: answer for answer in answers}
            questions = prediction.input_conversation.questions
            if len(by_name) != len(answers) or set(by_name) != {question["name"] for question in questions}:
                raise JsonFormatError("Decisions returned missing or duplicate answers")
            for question in questions:
                if by_name[question["name"]]["type"] != question["type"]:
                    raise JsonFormatError(f"Invalid answer type for {question['name']}")
            explanation = {key: by_name[key]["choice"] for key in ("initial_analysis","reasoning")}
            choice = by_name["next_action"]["choice"]
            if choice in DecisionsRules.MISSING:
                return DecisionOutput(action="Ask", missing_choice=DecisionsRules.MISSING[choice], **explanation)
            return DecisionOutput(action=choice, **explanation)
        except (ValueError, KeyError, TypeError) as error:
            raise JsonFormatError(str(error)) from error

    def classify(self, classifier_input: ClassifierInput,
                 predictor_metadata: LoggerMetadata | None = None) -> ClassifierOutput:
        start = perf_counter()
        prediction = None
        try:
            conversation = self._build_conversation(classifier_input)
            prediction = self.llm_handler.predict(
                conversation=conversation, timeout=DecisionsPrompt.REQUEST_TIMEOUT,
            )
            result = self._parse_prediction_output(prediction, classifier_input)
            return ClassifierOutput(
                result=result,
                token_usage=prediction.token_usage,
                llm_duration=perf_counter() - start,
                decisions_response=prediction.decisions_response,
            )
        except ConversationError as error:
            message = str(error)
            PredictorLogger.log_error(predictor_metadata, message)
            return ClassifierOutput(
                error_code=ErrorCode.ERROR_BUILDING_CONVERSATION,
                error_message=message,
                llm_duration=perf_counter() - start,
            )
        except OpenAiRecoverableError as error:
            message = ErrorMessages.LLM_ERROR.format(error)
            PredictorLogger.log_error(predictor_metadata, message)
            return ClassifierOutput(
                error_code=ErrorCode.LLM_RECOVERABLE_ERROR,
                error_message=message,
                llm_duration=perf_counter() - start,
            )
        except (OpenAiUnRecoverableError, OpenAIGeneralError) as error:
            message = ErrorMessages.LLM_ERROR.format(error)
            PredictorLogger.log_error(predictor_metadata, message)
            return ClassifierOutput(
                error_code=ErrorCode.LLM_UNRECOVERABLE_ERROR,
                error_message=message,
                llm_duration=perf_counter() - start,
            )
        except JsonFormatError as error:
            message = ErrorMessages.INVALID_LLM_RESPONSE.format(error)
            PredictorLogger.log_error(predictor_metadata, message)
            return ClassifierOutput(
                error_code=ErrorCode.INVALID_LLM_RESPONSE,
                error_message=message,
                token_usage=prediction.token_usage if prediction else None,
                llm_duration=perf_counter() - start,
                decisions_response=prediction.decisions_response if prediction else None,
            )
        except Exception as error:
            message = ErrorMessages.UNEXPECTED_ERROR.format(error)
            PredictorLogger.log_error(predictor_metadata, message)
            return ClassifierOutput(
                error_code=ErrorCode.UNEXPECTED_ERROR,
                error_message=message,
                token_usage=prediction.token_usage if prediction else None,
                llm_duration=perf_counter() - start,
                decisions_response=prediction.decisions_response if prediction else None,
            )
