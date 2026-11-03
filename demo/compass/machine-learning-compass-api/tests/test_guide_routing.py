from unittest import TestCase
from unittest.mock import Mock, patch
from compass.predictor import Predictor as Compass
from compass.predictor_input import PredictorInput as CompassInput
from api_objects.faro.signal.output.signal_output import SignalOutput


class GuideRoutingTests(TestCase):
    def test_other_routes_never_call_guide(self):
        for action in ("Continue", "Unsupported"):
            with self.subTest(action=action):
                guide, signal = Mock(), Mock()
                signal.classify.return_value = SignalOutput(action=action)
                compass = Compass(Mock(), Mock(), Mock(), Mock(), signal, guide, Mock(), Mock(), Mock(), Mock())
                # Other service outputs are outside this routing test.
                with patch("compass.predictor.PredictorOutput"), patch("compass.predictor.TurnCache") as cache:
                    cache.return_value.lookup.return_value = (None, None)
                    cache.return_value.ai.side_effect = lambda service, inputs, model, predict, *args: predict()
                    compass._answer(CompassInput(user_id="maria", question="Which cranes?"), Mock(), [], "test", {"_id":"test","cache":[]})
                guide.generate_followup.assert_not_called()
