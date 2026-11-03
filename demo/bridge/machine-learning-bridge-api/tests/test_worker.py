from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from bridge.source import run_read


class WorkerTests(TestCase):
    def test_general_pandas_and_table_result(self):
        records=[{"site":"A","n":10},{"site":"A","n":20},{"site":"B","n":30}]
        result=run_read("df.groupby('site')['n'].agg(['median','max'])",records,["site","n"])
        self.assertEqual(result,[{"site":"A","median":15,"max":20},{"site":"B","median":30,"max":30}])

    def test_expression_cannot_open_host_files(self):
        with TemporaryDirectory() as tmp:
            file=Path(tmp)/"other-company.json"
            file.write_text('[{"value":99}]')
            with self.assertRaises(ValueError):
                run_read(f"(df,pd.read_json({str(file)!r}))[1]",[{"value":1}],["value"])

    def test_large_result_is_not_cut_off(self):
        records=[{"n":i,"description":"x"*60} for i in range(6000)]
        self.assertEqual(run_read("df",records,["n","description"]),records)

    def test_long_expression_can_run(self):
        expression="df['n'].sum()" + " + 0"*210
        self.assertEqual(run_read(expression,[{"n":4}],["n"]),[{"value":4}])

    def test_worker_has_no_wall_clock_timeout(self):
        from unittest.mock import patch, Mock
        with patch("bridge.source.subprocess.run", return_value=Mock(returncode=0, stdout='[{"value":4}]')) as run:
            run_read("len(df)",[{"n":4}],["n"])
        self.assertNotIn("timeout",run.call_args.kwargs)
