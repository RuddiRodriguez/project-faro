from unittest.mock import Mock
from tests_support import ConnectedTest
from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import Read
from api_objects.faro.shield.input.shield_input import ShieldInput
from bridge.source import execute
from shield.verifier import Verifier


class SectorTests(ConnectedTest):
    def test_same_read_and_check_for_hospitals_and_hotels(self):
        for company,scopes,expected in [("cedar",["riverside","hillview"],2),("meridian",["madrid","tokyo","mexico_city"],3)]:
            request=BridgeInput(company_id=company,permitted_scope_ids=scopes,question="How many locations?")
            read=Read(source=company+"/assets",scope_ids=[],member_ids=[],group="",start=None,end_exclusive=None,expression="len(df)")
            evidence=execute(self.root,request,read)
            self.assertEqual(evidence.rows,[{"value":expected}])
            model=Mock();model.predict.return_value.assistant_tools=[Mock(parsed_arguments=dict(initial_analysis="Counted rows.",reasoning="Count matches.",decision="supported",reason="Matches."))]
            self.assertEqual(Verifier(self.root,model).verify(ShieldInput(**request.model_dump(),evidence=evidence)).status,"verified")
            restricted=request.model_copy(update={"permitted_scope_ids":scopes[:1]})
            self.assertEqual(Verifier(self.root,model).verify(ShieldInput(**restricted.model_dump(),evidence=evidence)).status,"withheld")
