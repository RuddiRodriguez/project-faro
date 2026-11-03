from api_objects.faro.thread.input.plan_input import PlanInput
from api_objects.faro.thread.output.plan_output import PlanOutput
from thread.predictor_files.ranking_prompt import RankingPrompt
from utils.llms.common.intelligence_level import IntelligenceLevel
from utils.openai_client.conversation.conversation import Conversation
from utils.openai_client.conversation.system_message import SystemMessage
from utils.openai_client.conversation.user_message import UserMessage


class Planner:
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler

    def predict(self, request: PlanInput) -> PlanOutput:
        conversation = Conversation(intelligence_level=IntelligenceLevel.LIGHT,
            system_message=SystemMessage(content=RankingPrompt.SYSTEM_MESSAGE))
        conversation.add_message(UserMessage(content=request.model_dump_json()))
        prediction = self.llm_handler.predict(conversation=conversation, structured_output=RankingPrompt.STRUCTURED_OUTPUT,
                                              timeout=30, enable_auto_fix_json=False)
        if not prediction.is_success or not prediction.assistant_tools:
            raise ValueError("Plan prediction returned no structured result")
        result = PlanOutput.model_validate(prediction.assistant_tools[0].parsed_arguments)
        selected = result.selected_definition_id
        if selected is not None and selected not in request.documented_choices:
            raise ValueError("Selected definition does not belong to this company")
        if selected in request.ranking_definition_ids and selected not in request.definitions:
            raise ValueError("Search did not supply the evidence for the selected measure")
        if selected is not None and selected not in request.ranking_definition_ids:
            return PlanOutput(status="unavailable", selected_definition_id=selected, ranking=None,
                              reason=f"{request.documented_choices[selected]} is documented but unavailable for this ranking.")
        if result.status == "unavailable" and selected is None and request.selected_measure and result.reason:
            return PlanOutput(status="unavailable", selected_definition_id=None, ranking=None, reason=result.reason)
        if result.status == "unavailable":
            raise ValueError("Unavailable choice was not identified")
        if result.status == "ready":
            plan = result.ranking
            if (not plan or (selected and plan.definition_id != selected) or plan.definition_id not in request.definitions or plan.group not in request.groups
                    or not plan.scope_ids or not set(plan.scope_ids).issubset(request.scopes)
                    or not set(plan.member_ids).issubset(request.groups[plan.group]) or plan.start >= plan.end_exclusive):
                return PlanOutput(status="unsupported", selected_definition_id=selected, ranking=None, reason="The choices do not match the permitted company information.")
        elif result.ranking is not None or not result.reason:
            raise ValueError("Incomplete plan decision")
        return result
