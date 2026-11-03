import json
import logging

from guide.common_tools.custom_exceptions import ConversationError, JsonFormatError
from guide.common_tools.error_code import ErrorCode
from utils.llms.llm_handler import LLMHandler
from utils.llms.common.intelligence_level import IntelligenceLevel
from guide.common_tools.log_messages import ErrorMessages
from guide.prompts.followup_prompt import FollowUp, FollowUpPrompt
from guide.followup.generator_input import GeneratorInput
from guide.followup.generator_output import GeneratorOutput

from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage
from utils.openai_client.exceptions import OpenAiRecoverableError, OpenAiUnRecoverableError
from utils.openai_client.outputs.predict_output import PredictOutput


class Generator:
    def __init__(self, llm_handler: LLMHandler) -> None:
        self.llm_handler = llm_handler
    
    def _build_conversation(self, generator_input: GeneratorInput) -> Conversation:
        try:
            conversation = Conversation(intelligence_level=IntelligenceLevel.YOLO,
                                        system_message=SystemMessage(content=FollowUpPrompt.SYSTEM_MESSAGE))

            user_msg_text = FollowUpPrompt.USER_MESSAGE.format(
                language=generator_input.language or "not specified",
                user_messages=json.dumps(generator_input.user_messages, ensure_ascii=False),
                question_text=json.dumps(generator_input.question_text, ensure_ascii=False),
                missing_choice=json.dumps(generator_input.missing_choice, ensure_ascii=False),
                definitions=json.dumps([d.model_dump() for d in generator_input.definitions], ensure_ascii=False),
            )

            user_message = UserMessage(content=user_msg_text.strip())
            conversation.add_message(user_message)

            return conversation
        except Exception as ex:
            raise ConversationError(
                ErrorMessages.ERROR_BUILDING_CONVERSATION.format(ex))

    def _parse_chat_prediction_output(self, chat_prediction: PredictOutput) -> FollowUp:
        parsed_arguments = None
        if chat_prediction.is_success:
            if chat_prediction.assistant_tools is not None and len(chat_prediction.assistant_tools) > 0:
                parsed_arguments = chat_prediction.assistant_tools[0].parsed_arguments

        if parsed_arguments is None:
            raise JsonFormatError(ErrorMessages.OPENAI_PARSED_ARGUMENTS_NULL)

        for key in FollowUpPrompt.REQUIRED_KEYS:
            if key not in parsed_arguments:
                raise JsonFormatError(
                    ErrorMessages.KEY_MISSING_FROM_ASSISTANT_TOOLS.format([key]))

        generated_followup_text_value = parsed_arguments[FollowUpPrompt.SELECTED_GENERATOR_KEY]
        if not generated_followup_text_value or not isinstance(generated_followup_text_value, str):
            raise JsonFormatError(
                 ErrorMessages.ERROR_INCORRECT_TYPE.format(generated_followup_text_value,  type(generated_followup_text_value)))

        result = FollowUp.model_validate(parsed_arguments)
        return result

    def generate_followup(self, generator_input: GeneratorInput) -> GeneratorOutput:

        try:
            conversation = self._build_conversation(generator_input)
            chat_prediction = self.llm_handler.predict(
                conversation=conversation, structured_output=FollowUpPrompt.STRUCTURED_OUTPUT,
                timeout=30, enable_auto_fix_json=False)
            proposal = self._parse_chat_prediction_output(chat_prediction)

            return GeneratorOutput(initial_analysis=proposal.initial_analysis, followup_text=proposal.follow_up,
                                    followup_reasoning=proposal.reasoning,
                                    error_code=None
                                    )
        
        # Handle conversation error from _build_conversation
        except ConversationError as ex:
            logging.getLogger(__name__).error(ErrorMessages.ERROR_BUILDING_CONVERSATION.format(ex))
            return GeneratorOutput(followup_reasoning = None,
                                    followup_text = None,
                                    error_code = ErrorCode.ERROR_BUILDING_CONVERSATION,
                                    )
        # Handle OpenAI error
        except (OpenAiRecoverableError, OpenAiUnRecoverableError) as ex:

            logging.getLogger(__name__).error(ErrorMessages.ERROR_GENERATING_FOLLOWUP.format(ex))

            return GeneratorOutput(followup_reasoning = None,
                                    followup_text = None,
                                    error_code = ErrorCode.OPENAI_ERROR,
                                    )
        # Handle json format error
        except JsonFormatError as ex:

            logging.getLogger(__name__).error(ErrorMessages.ERROR_GENERATING_FOLLOWUP.format(ex))

            return GeneratorOutput(followup_reasoning = None,
                                    followup_text = None,
                                    error_code = ErrorCode.INVALID_LLM_RESPONSE,
                                    )

        # Handle any other exception
        except Exception as ex:

            logging.getLogger(__name__).error(ErrorMessages.ERROR_GENERATING_FOLLOWUP.format(ex))

            return GeneratorOutput(followup_reasoning = None,
                                    followup_text = None,
                                    error_code = ErrorCode.GENERAL_ERROR_GENERATING_FOLLOWUP,
                                    )

