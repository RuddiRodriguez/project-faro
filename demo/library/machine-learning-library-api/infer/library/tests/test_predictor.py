import json
import tempfile
import unittest
from pathlib import Path

from library.information_reader import InformationReader
from library.information_reader_input import InformationReaderInput

DATA = Path(__file__).resolve().parents[5] / 'local_data/demo_dataset'


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name)
        for name in ['companies', 'scopes', 'documents', 'agreements', 'assets', 'manifest']:
            (self.path / f'{name}.json').write_text((DATA / f'{name}.json').read_text())
        self.information_reader = InformationReader(self.path)

    def read(self, company='harbor', scopes=None):
        return self.information_reader.read(InformationReaderInput(
            company_id=company,
            permitted_scope_ids=scopes if scopes is not None else [f'{company}_north']))

    def test_company_and_terminal_separation(self):
        for company in ['harbor', 'pacific', 'strait']:
            with self.subTest(company=company):
                result = self.read(company)
                self.assertEqual(result.company.company_id, company)
                self.assertEqual([item.scope_id for item in result.scopes], [f'{company}_north'])
                self.assertEqual(len(result.documents), 4)
                self.assertEqual(len(result.agreements), 1)
                for item in result.documents:
                    self.assertEqual(item.company_id, company)
                    self.assertEqual(item.scope_ids, [f'{company}_north'])
                self.assertEqual(result.agreements[0].scope_id, f'{company}_north')

    def test_both_scopes_and_no_permissions(self):
        result = self.read(scopes=['harbor_north', 'harbor_south'])
        self.assertEqual(len(result.scopes), 2)
        self.assertEqual(len(result.agreements), 2)
        result = self.read(scopes=[])
        self.assertEqual((result.scopes, result.documents, result.agreements), ([], [], []))

    def test_unknown_company_or_wrong_terminal(self):
        with self.assertRaisesRegex(ValueError, 'Company not found'):
            self.read('unknown')
        for terminal in ['pacific_north', 'missing']:
            with self.assertRaisesRegex(ValueError, 'does not belong'):
                self.read(scopes=[terminal])

    def test_unapproved_and_other_terminal_material_is_excluded(self):
        for name in ['documents', 'agreements']:
            path = self.path / f'{name}.json'
            items = json.loads(path.read_text())
            draft = {**items[0], 'status': 'draft'}
            items.append(draft)
            if name == 'documents':
                items.append({**items[0], 'scope_ids': ['harbor_south'], 'text': 'South only'})
            path.write_text(json.dumps(items))
        result = self.read()
        self.assertEqual(len(result.documents), 4)
        self.assertEqual(len(result.agreements), 1)

    def test_saved_updates_are_read_on_next_call(self):
        path = self.path / 'companies.json'
        items = json.loads(path.read_text())
        items[0]['data_version'] = 'updated'
        path.write_text(json.dumps(items))
        self.assertEqual(self.read().company.data_version, 'updated')


if __name__ == '__main__':
    unittest.main()
