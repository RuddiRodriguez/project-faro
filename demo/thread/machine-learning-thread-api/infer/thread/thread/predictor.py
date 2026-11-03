from utils.llms.llm_handler import LLMHandler
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage
from utils.openai_client.outputs.predict_output import PredictOutput

from thread.predictor_input import PredictorInput
from thread.predictor_output import PredictorOutput
from thread.predictor_files.standalone_query_prompt import RewrittenQuestion, StandaloneQueryPrompt


class Predictor:
    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler

    def _build_conversation(self, predictor_input: PredictorInput) -> Conversation:
        conversation = Conversation(
            intelligence_level=IntelligenceLevel.YOLO,
            system_message=SystemMessage(content=StandaloneQueryPrompt.SYSTEM_MESSAGE))
        history = "\n".join(f"{message.role}: {message.content}"
                            for message in predictor_input.conversation)
        user_message = StandaloneQueryPrompt.USER_MESSAGE.format(
            conversation=history, question=predictor_input.question)
        conversation.add_message(UserMessage(content=user_message))
        return conversation

    def _parse_chat_prediction_output(self, chat_prediction: PredictOutput) -> RewrittenQuestion:
        parsed_arguments = None
        if chat_prediction.is_success:
            if chat_prediction.assistant_tools is not None and len(chat_prediction.assistant_tools) > 0:
                parsed_arguments = chat_prediction.assistant_tools[0].parsed_arguments

        if parsed_arguments is None:
            raise ValueError("Prediction contains no parsed arguments")

        parsed_output = RewrittenQuestion.model_validate(parsed_arguments)
        return parsed_output

    def predict(self, predictor_input: PredictorInput) -> PredictorOutput:
        if not predictor_input.conversation:
            return PredictorOutput(question=predictor_input.question, used_ai=False)

        conversation = self._build_conversation(predictor_input)
        chat_prediction = self.llm_handler.predict(
            conversation=conversation,
            structured_output=StandaloneQueryPrompt.STRUCTURED_OUTPUT,
            timeout=30,
            enable_auto_fix_json=False)
        rewrite = self._parse_chat_prediction_output(chat_prediction)
        return PredictorOutput(question=rewrite.question, unclear_references=rewrite.unclear_references, used_ai=True,
                               model_name=chat_prediction.input_conversation.llm_model_name,
                               token_usage=chat_prediction.token_usage)
