from api_objects.faro.thread.input.plan_input import PlanInput
from api_objects.faro.thread.output.plan_output import PlanOutput
from compass_api.external_services.http_caller_with_exception_on_error import call
from api_objects.faro.thread.input.thread_input import ThreadInput, ConversationMessage
from api_objects.faro.thread.output.thread_output import ThreadOutput


from api_objects.faro.thread.input.turn_input import TurnInput
from api_objects.faro.thread.output.turn_output import TurnOutput


class ThreadClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = "Thread"

    def rewrite_question(self, question: str, conversation) -> ThreadOutput:
        request = ThreadInput(question=question,
                              conversation=[ConversationMessage(role=message.role, content=message.content)
                                            for message in conversation])
        return call(self.service_name, self.base_url, "/v1/rewrite", request, ThreadOutput, timeout=100)

    def update_turn(self, question, history, state, proposal):
        request = TurnInput(question=question, current_request=state, proposed_changes=proposal,
            conversation=[ConversationMessage(role=m.role, content=m.content) for m in history])
        return call(self.service_name, self.base_url, "/v1/turn", request, TurnOutput, timeout=100)

    def prepare_ranking(self, search, information, selected_measure) -> PlanOutput:
        request = PlanInput(question=search.query, selected_measure=selected_measure, reference_date=information.reference_date, supported_tasks=information.supported_tasks,
                            definitions={m.document_id: m.text for m in search.matches if m.document_id in information.ranking_definition_ids},
                            ranking_definition_ids=information.ranking_definition_ids,
                            documented_choices={m.document_id: m.title for m in information.documents},
                            scopes={s.scope_id: s.name for s in information.scopes}, groups=information.groups)
        return call(self.service_name, self.base_url, "/v1/ranking", request, PlanOutput, timeout=100)
