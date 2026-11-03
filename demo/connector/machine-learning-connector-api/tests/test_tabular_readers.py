import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import pandas as pd
from connector.source_reader import SourceReader
from connector.source_reader_input import SourceReaderInput


class TabularReadersTests(TestCase):
    def test_formats_permissions_versions_and_no_partial_results(self):
        for extension in ("csv", "parquet"):
            with self.subTest(extension=extension), TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / f"records.{extension}"
                frame = pd.DataFrame(dict(scope=["north", "south"], identifier=["001", "002"], value=[1.25, 2.5]))
                def save(data):
                    if extension == "csv":
                        data.to_csv(path, index=False)
                    else:
                        data.to_parquet(path, index=False)
                save(frame)
                (root / "connections.json").write_text(json.dumps([dict(company="client", scopes=["north", "south"],
                    file=path.name, scope_field="scope")]))
                reader = SourceReader(root)
                request = SourceReaderInput(company_id="client", permitted_scope_ids=["north"], action="read", item="records/rows")
                with patch.dict(os.environ, FARO_DOCUMENT_PATH=str(root / "saved")):
                    result = reader.read(request)
                    self.assertEqual(len(result.rows), 1)
                    self.assertEqual(result.rows[0]["identifier"], "001")
                    self.assertEqual(float(result.rows[0]["value"]), 1.25)
                    self.assertIn("record 1", result.references[0])
                    from urllib.parse import urlparse, unquote
                    exported = json.loads(Path(unquote(urlparse(result.document["uri"]).path)).read_text())
                    self.assertEqual(len(exported["rows"]), 1)
                    with self.assertRaises(PermissionError):
                        reader.read(request.model_copy(update={"company_id":"other"}))
                    projected = reader.read(request.model_copy(update={"fields":["identifier"]}))
                    self.assertEqual(projected.rows, [{"identifier":"001"}])
                    old = result.items[0].version
                    save(pd.concat([frame.iloc[[0]]] * 1002, ignore_index=True))
                    self.assertNotEqual(reader.read(request.model_copy(update={"action":"inspect"})).items[0].version, old)
                    self.assertEqual(len(reader.read(request).rows),1002)
