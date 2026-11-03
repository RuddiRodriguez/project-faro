from unittest import TestCase
from unittest.mock import Mock

from api_objects.faro.thread.input.plan_input import PlanInput
from thread.planner import Planner


class RankingAvailabilityTests(TestCase):
    def test_documented_choice_vs_missing_evidence(self):
        request = PlanInput(question="Use occupancy", reference_date="2026-11-01", supported_tasks=["Rank properties"],
            definitions={}, ranking_definition_ids=[], documented_choices={"occ": "Occupancy"}, groups={}, scopes={})
        handler = Mock()
        handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={
            "status":"ask", "ranking":None, "reason":"Which measure?", "selected_definition_id":"occ"})]
        planner = Planner(handler)
        self.assertEqual(planner.predict(request).status, "unavailable")
        request.ranking_definition_ids = ["occ"]
        with self.assertRaisesRegex(ValueError, "Search did not supply"):
            planner.predict(request)

    def test_confirmation_changes_only_proposed_and_explicit_fields(self):
        from api_objects.faro.thread.input.turn_input import TurnInput
        from thread.turn import update_turn

        request = TurnInput(question="Yes, but for last quarter", conversation=[{"role":"assistant","content":"Use recycling rate?"}],
            current_request={"subjects":"districts","period":"this quarter","scope":"north"},
            proposed_changes=[{"field":"measure","value":"recycling rate"}])
        handler = Mock()
        handler.predict.return_value.assistant_tools = [Mock(parsed_arguments={
            "action":"accept", "changes":[{"field":"period","value":"last quarter"}], "unclear_references":[]})]
        handler.predict.return_value.token_usage = None
        self.assertEqual(update_turn(request, handler).current_request,
            {"subjects":"districts","scope":"north","measure":"recycling rate","period":"last quarter"})
        self.assertEqual(request.current_request["period"], "this quarter")
