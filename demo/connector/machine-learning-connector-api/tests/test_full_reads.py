import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch
from openpyxl import Workbook
from api_objects.faro.connector.input.connector_input import ConnectorInput
from connector.readers import SQLite, Excel, PDF
from connector.source_reader import SourceReader


class FullReadTests(TestCase):
    def test_sqlite_and_excel_keep_rows_after_one_thousand(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            with sqlite3.connect(root/'records.sqlite') as db:
                db.execute('CREATE TABLE records (value INTEGER)')
                db.executemany('INSERT INTO records VALUES (?)',[(i,) for i in range(1002)])
            book=Workbook(); sheet=book.active; sheet.title='records'
            sheet.append(['value'])
            for i in range(1002):
                sheet.append([i])
            book.save(root/'records.xlsx')
            for reader in (SQLite(root/'records.sqlite'),Excel(root/'records.xlsx')):
                rows,refs=reader.read('records',['value'])
                self.assertEqual(len(rows),1002)
                self.assertEqual(rows[-1],{'value':1001})
                self.assertEqual(len(refs),1002)

    def test_pdf_keeps_pages_after_one_thousand(self):
        page=Mock();page.extract_text.return_value='Source text'
        with patch('connector.readers.PdfReader',return_value=Mock(pages=[page]*1002)):
            rows,refs=PDF(Path('report.pdf')).read('pages',['page','text'])
        self.assertEqual(rows[-1]['page'],1002)
        self.assertEqual(refs[-1],'page 1002')

    def test_connector_returns_all_permitted_rows(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'records.json').write_text(json.dumps({'records':[{'scope':'allowed','value':i} for i in range(1002)]}))
            (root/'connections.json').write_text(json.dumps([dict(company='test',scopes=['allowed'],file='records.json',scope_field='scope')]))
            with patch.dict('os.environ',FARO_DOCUMENT_PATH=str(root/'saved')):
                result=SourceReader(root).read(ConnectorInput(company_id='test',permitted_scope_ids=['allowed'],action='read',item='records/records'))
            self.assertEqual(len(result.rows),1002)
            self.assertEqual(result.rows[-1]['value'],1001)
