from pathlib import Path
from threading import Barrier, Event
from unittest import TestCase
from unittest.mock import Mock, patch

from api_objects.faro.bridge.output.bridge_output import BridgeOutput, Observation, Read
from shield.verifier import Verifier
from shield.verifier_input import VerifierInput
from utils.llms.model_attempts import turn_context


class ParallelReadTests(TestCase):
    def setUp(self):
        self.reads=[Read(source=name,scope_ids=[],member_ids=[],group='',start=None,end_exclusive=None,
                         expression='len(df)') for name in ('first','second')]
        self.observations=[Observation(status='ready',company_id='test',question='How many?',read=read,
                                       rows=[{'value':i}]) for i,read in enumerate(self.reads,1)]
        self.evidence=BridgeOutput(**self.observations[0].model_dump(),supporting=self.observations[1:])
        self.request=VerifierInput(company_id='test',permitted_scope_ids=['site'],question='How many?',evidence=self.evidence)
        self.model=Mock()
        self.model.predict.return_value=Mock(is_success=True,assistant_tools=[Mock(parsed_arguments={
            'initial_analysis':'Results agree.', 'reasoning':'Both reads match.', 'decision':'supported','reason':'Both reads match.'})])
        self.verifier=Verifier(Path('.'),self.model)

    def run_verification(self, execute):
        with patch('shield.verifier.catalogue',return_value={'scopes':['site']}), patch('shield.verifier.execute',side_effect=execute):
            return self.verifier.verify(self.request)

    def test_reads_overlap_keep_order_and_request_context(self):
        barrier=Barrier(2); second_done=Event(); seen=[]
        token=turn_context.set(('test','turn','Shield'))
        def execute(path,request,read):
            seen.append(turn_context.get())
            barrier.wait(timeout=5)
            if read.source=='first':
                self.assertTrue(second_done.wait(5))
                return self.observations[0]
            second_done.set()
            return self.observations[1]
        try:
            result=self.run_verification(execute)
        finally:
            turn_context.reset(token)
        self.assertEqual(result.status,'verified')
        self.assertEqual(seen,[('test','turn','Shield')]*2)
        prompt=self.model.predict.call_args.kwargs['conversation'].messages[0].content
        self.assertLess(prompt.index('first'),prompt.index('second'))
        self.model.predict.assert_called_once()

    def test_changed_result_stops_before_model_review(self):
        def execute(path,request,read):
            obs=self.observations[0 if read.source=='first' else 1]
            return obs.model_copy(update={'rows':[{'value':999}]}) if read.source=='second' else obs
        result=self.run_verification(execute)
        self.assertEqual(result.status,'withheld')
        self.model.predict.assert_not_called()

    def test_read_failure_stops_before_model_review(self):
        for error in (ValueError('Source changed'),PermissionError('Access denied')):
            with self.subTest(error=error):
                def execute(path,request,read):
                    if read.source=='second':
                        raise error
                    return self.observations[0]
                result=self.run_verification(execute)
                self.assertEqual(result.status,'withheld')
                self.assertEqual(result.reason,str(error))
        self.model.predict.assert_not_called()
