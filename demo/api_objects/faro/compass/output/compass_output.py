from pydantic import BaseModel

from api_objects.faro.voice.output.voice_output import VoiceOutput
from api_objects.faro.shield.output.shield_output import ShieldOutput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput
from api_objects.faro.guide.output.guide_output import GuideOutput
from api_objects.faro.gate.output.gate_output import GateOutput
from api_objects.faro.connector.output.connector_output import ConnectorOutput
from api_objects.faro.thread.output.thread_output import ThreadOutput
from api_objects.faro.scout.output.scout_output import ScoutOutput


from api_objects.faro.signal.output.signal_output import SignalOutput




class CompassOutput(BaseModel):
    conversation_id: str
    turn_id: str
    question: str
    access: GateOutput
    sources: ConnectorOutput
    rewrite: ThreadOutput
    search: ScoutOutput
    decision: SignalOutput
    followup: GuideOutput | None = None
    evidence: BridgeOutput | None = None
    verification: ShieldOutput | None = None
    answer: VoiceOutput | None = None
