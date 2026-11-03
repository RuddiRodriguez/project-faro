from api_objects.faro.compass.input.compass_input import CompassInput as ApiOrchestratorInput
from api_objects.faro.compass.output.compass_output import CompassOutput as ApiOrchestratorOutput
from compass.orchestrator import Orchestrator
from compass.orchestrator_input import OrchestratorInput as LibOrchestratorInput, ConversationMessage as LibConversationMessage


class OrchestratorEndpoint:
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator

    def handle(self, api_input: ApiOrchestratorInput) -> ApiOrchestratorOutput:
        orchestrator_input = LibOrchestratorInput(conversation_id=api_input.conversation_id, previous_answer_id=api_input.previous_answer_id, user_id=api_input.user_id,
                                            question=api_input.question, language=api_input.language,
                                            conversation=[LibConversationMessage(role=message.role, content=message.content)
                                                          for message in api_input.conversation])
        result = self.orchestrator.orchestrate(orchestrator_input)
        return ApiOrchestratorOutput(conversation_id=result.conversation_id, turn_id=result.turn_id, question=result.question,
                                  access=result.access,
                                  sources=result.sources,
                                  rewrite=result.rewrite,
                                  search=result.search,
                                  decision=result.decision, followup=result.followup, evidence=result.evidence, verification=result.verification, answer=result.answer)
