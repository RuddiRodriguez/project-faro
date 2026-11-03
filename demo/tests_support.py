import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from api_objects.faro.connector.input.connector_input import ConnectorInput
from connector.source_reader import SourceReader


class ConnectedTest(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(Path(__file__).parent/"connector/fixtures",self.root,dirs_exist_ok=True)
        reader = SourceReader(self.root)
        def sources(company,scopes,action="discover",item=None):
            return reader.read(ConnectorInput(company_id=company,permitted_scope_ids=scopes,action=action,item=item))
        for target in ("bridge.source.connected_sources","bridge.connected.sources"):
            replacement = patch(target,side_effect=sources)
            replacement.start();self.addCleanup(replacement.stop)
        setting=patch.dict(os.environ,FARO_DOCUMENT_PATH=str(self.root/"copies"))
        setting.start();self.addCleanup(setting.stop)
