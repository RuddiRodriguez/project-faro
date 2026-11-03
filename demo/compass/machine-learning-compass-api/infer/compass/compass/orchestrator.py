from utils.llms.model_attempts import turn_context
from time import monotonic
from uuid import uuid4

from api_objects.faro.bridge.output.bridge_output import BridgeOutput
from api_objects.faro.guide.output.guide_output import GuideOutput
from api_objects.faro.signal.output.signal_output import SignalOutput
from api_objects.faro.thread.output.thread_output import ThreadOutput
from api_objects.faro.voice.output.voice_output import VoiceOutput
from compass.data_collection import ConversationInputError, TurnCache, now
from compass.orchestrator_input import OrchestratorInput, ConversationMessage
from compass.orchestrator_output import OrchestratorOutput


class Orchestrator:
    def __init__(self, gate_client, connector_client, thread_client, scout_client, signal_client, guide_client, bridge_client, shield_client, voice_client, collection):
        self.gate_client = gate_client
        self.connector_client = connector_client
        self.thread_client = thread_client
        self.scout_client = scout_client
        self.voice_client = voice_client
        self.shield_client = shield_client
        self.bridge_client = bridge_client
        self.guide_client = guide_client
        self.signal_client = signal_client
        self.collection = collection

    def orchestrate(self, orchestrator_input: OrchestratorInput) -> OrchestratorOutput:
        access = self.gate_client.read_access(orchestrator_input.user_id)
        with self.collection.conversation(orchestrator_input, access) as doc:
            if orchestrator_input.conversation_id and doc["turns"] and doc["turns"][-1]["status"] not in {"Ask", "failed"}:
                raise ConversationInputError("This request is closed. Start a new question without a conversation ID.")
            history = [ConversationMessage.model_validate(m) for m in doc["messages"]]
            turn = dict(_id=str(uuid4()), number=len(doc["turns"])+1, message=orchestrator_input.question,
                        created_at=now().isoformat(), cache=[], model_attempts_tracked=True, status="started")
            doc["turns"].append(turn)
            doc["messages"].append(dict(role="user", content=orchestrator_input.question))
            self.collection.save_conversation(doc)
            token = turn_context.set((access.company_id, turn["_id"], "Compass"))
            start = monotonic()
            try:
                result = self._answer(orchestrator_input, access, history, doc["_id"], turn,
                                      next((t for t in reversed(doc["turns"][:-1]) if t.get("response")), {}))
                reply = (result.followup.followup_text if result.followup else
                         result.answer.text if result.answer else None)
                turn.update(status=result.verification.status if result.verification else result.decision.action,
                            response=result.model_dump(mode="json", exclude={"sources", "access"}))
                if reply:
                    doc["messages"].append(dict(role="assistant", content=reply))
                return result
            except Exception as exc:
                turn.update(status="failed", error="; ".join(getattr(exc, "__notes__", []) or [type(exc).__name__]))
                raise
            finally:
                turn_context.reset(token)
                turn["elapsed_ms"] = round((monotonic()-start)*1000)
                self.collection.save_conversation(doc)

    def _answer(self, request, access, history, conversation_id, turn, previous=None):
        info = self.connector_client.discover_sources(access)
        cache = TurnCache(self.collection, access, info, turn["cache"], turn["_id"],
                          opening=not history and not request.conversation_id)
        question = request.question
        if history:
            rewrite = self.thread_client.rewrite_question(question, history)
        else:
            rewrite = ThreadOutput(question=question, used_ai=False)
        search = self.scout_client.search_sources(rewrite.question, access)
        def classify():
            return self.signal_client.classify(search, access, rewrite.unclear_references)
        decision = (cache.ai("Signal", [search, rewrite.unclear_references], SignalOutput, classify)
                    if not rewrite.unclear_references else classify())
        turn["decision_source"] = "Signal"
        answer = followup = verification = evidence = None
        if decision.action == "Continue":
            key, evidence = cache.lookup("data", "Bridge", [rewrite.question, search], BridgeOutput)
            if evidence is not None:
                verification = self.shield_client.verify_evidence(access, rewrite.question, evidence)
                if verification.status != "verified":
                    self.collection.discard(access.company_id, "data", key)
                    turn["cache"][-1]["result_source"] = "rejected"
                    evidence = verification = None
            if evidence is None:
                evidence = self.bridge_client.read_evidence(access, rewrite.question, search.matches)
            turn["decision_source"] = "Bridge"
            turn["plan"] = evidence.read.model_dump(mode="json") if evidence.read else None
            if evidence.status == "ask":
                decision = SignalOutput(action="Ask", missing_choice=evidence.reason)
            elif evidence.status == "not_supported":
                decision = SignalOutput(action="Unsupported")
                answer = VoiceOutput(status="withheld", text=evidence.reason, sources=[], mode="direct")
            else:
                if verification is None:
                    verification = self.shield_client.verify_evidence(access, rewrite.question, evidence)
                    if key and verification.status == "verified":
                        self.collection.save_to_cache(access.company_id, "data", key, "Bridge", verification.facts, turn["_id"])
                        turn["cache"][-1]["produced_by_turn"] = turn["_id"]
                def write_answer():
                    return self.voice_client.write_answer(rewrite.question, verification, search)
                answer = (cache.ai("Voice", [rewrite.question, verification, search], VoiceOutput,
                                   write_answer, lambda r: r.mode == "ai")
                          if verification.status == "verified" else write_answer())
        elif decision.action == "Unsupported":
            answer = VoiceOutput(status="withheld", text="I can only answer questions about your company data.", sources=[], mode="direct")
        if decision.action == "Ask":
            options = search
            user_messages = [m.content for m in history if m.role == "user"][-2:] + [question]
            followup = cache.ai("Guide", [options, user_messages, decision.missing_choice, rewrite.unclear_references], GuideOutput,
                lambda: self.guide_client.generate_followup(options, decision.missing_choice, rewrite.unclear_references, user_messages, search.matches))
        return OrchestratorOutput(conversation_id=conversation_id, turn_id=turn["_id"], question=question, access=access,
            sources=info, rewrite=rewrite, search=search, decision=decision, followup=followup,
            evidence=verification.facts if verification else None, verification=verification, answer=answer)
