from unittest import TestCase
from unittest.mock import Mock, patch
from compass.orchestrator import Orchestrator as Compass
from compass.orchestrator_input import OrchestratorInput as CompassInput
from api_objects.faro.signal.output.signal_output import SignalOutput


class GuideRoutingTests(TestCase):
    def test_shared_api_caller_is_available(self):
        from compass_api.external_services.http_caller_with_exception_on_error import call
        from utils.service_call import call as shared_call
        self.assertIs(call, shared_call)

    def test_other_routes_never_call_guide(self):
        for action in ("Continue", "Unsupported"):
            with self.subTest(action=action):
                guide, signal = Mock(), Mock()
                signal.classify.return_value = SignalOutput(action=action)
                compass = Compass(Mock(), Mock(), Mock(), Mock(), signal, guide, Mock(), Mock(), Mock(), Mock())
                # Other service outputs are outside this routing test.
                with patch("compass.orchestrator.OrchestratorOutput"), patch("compass.orchestrator.TurnCache") as cache:
                    cache.return_value.lookup.return_value = (None, None)
                    cache.return_value.ai.side_effect = lambda service, inputs, model, predict, *args: predict()
                    compass._answer(CompassInput(user_id="maria", question="Which cranes?"), Mock(), [], "test", {"_id":"test","cache":[]})
                guide.generate.assert_not_called()
