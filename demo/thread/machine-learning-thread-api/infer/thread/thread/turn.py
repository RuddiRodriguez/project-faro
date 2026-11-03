import json
from api_objects.faro.thread.output.turn_output import TurnOutput
from thread.predictor_files.turn_prompt import TurnEdit, TurnPrompt
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage


def update_turn(request, handler):
    conversation = Conversation(intelligence_level=IntelligenceLevel.LIGHT,
        system_message=SystemMessage(content=TurnPrompt.SYSTEM_MESSAGE))
    earlier = list(request.conversation)
    last_answer = earlier.pop().content if earlier and earlier[-1].role == "assistant" else None
    # Japan thread pattern: earlier context, then the newest assistant/user exchange.
    payload = dict(earlier_context=[m.model_dump() for m in earlier],
                   latest_exchange={"assistant": last_answer, "user": request.question},
                   current_request=request.current_request, proposed_changes=[c.model_dump() for c in request.proposed_changes])
    conversation.add_message(UserMessage(content=json.dumps(payload, ensure_ascii=False)))
    result = handler.predict(conversation=conversation, structured_output=TurnPrompt.STRUCTURED_OUTPUT,
                             timeout=30, enable_auto_fix_json=False)
    if not result.is_success or not result.assistant_tools:
        raise ValueError("Thread did not return a request update")
    edit = TurnEdit.model_validate(result.assistant_tools[0].parsed_arguments)
    state = {} if edit.action == "new" else request.current_request.copy()
    if edit.action in ("new", "update", "accept"):
        accepted = request.proposed_changes if edit.action == "accept" else []
        for change in [*accepted, *edit.changes]:
            if change.value is None:
                state.pop(change.field, None)
            else:
                state[change.field] = change.value
    question = "; ".join(state.values()) if state and edit.action in ("new", "update", "accept") else request.question
    if not request.conversation:
        question = request.question
    return TurnOutput(question=question, current_request=state, intent="unsupported" if edit.action == "unsupported" else "request", unclear_references=edit.unclear_references,
                      used_ai=True, token_usage=result.token_usage, model_name=conversation.llm_model_name)
