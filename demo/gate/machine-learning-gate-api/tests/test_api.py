import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from gate_api.infer import create_app
from library.information_reader import InformationReader as LibraryReader
from library.information_reader_input import InformationReaderInput as LibraryInput

DATA = Path(__file__).resolve().parents[3] / 'local_data/demo_dataset'


class GateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name)
        (self.path / 'users.json').write_text((DATA / 'users.json').read_text())
        self.client = TestClient(create_app(self.path))
        self.addCleanup(self.client.close)

    def access(self, user_id):
        return self.client.post('/v1/access', json={'user_id': user_id})

    def test_maria_permissions(self):
        response = self.access('maria')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'user_id': 'maria', 'company_id': 'harbor',
            'permitted_scope_ids': ['harbor_north', 'harbor_south'],
            'permission_version': 'v1'})

    def test_unknown_and_disabled_users_are_refused(self):
        for user_id in ['missing', 'former_user']:
            with self.subTest(user_id=user_id):
                self.assertEqual(self.access(user_id).status_code, 403)

    def test_empty_permissions_stay_empty(self):
        response = self.access('noah')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['permitted_scope_ids'], [])

    def test_company_and_permissions_come_from_saved_user(self):
        response = self.client.post('/v1/access', json={
            'user_id': 'ana', 'company_id': 'pacific',
            'permitted_scope_ids': ['pacific_north']})
        self.assertEqual(response.status_code, 200)
        access = response.json()
        self.assertEqual(access['company_id'], 'harbor')
        self.assertEqual(access['permitted_scope_ids'], ['harbor_north'])
        result = LibraryReader(DATA).read(LibraryInput(
            company_id=access['company_id'],
            permitted_scope_ids=access['permitted_scope_ids']))
        self.assertEqual([item.scope_id for item in result.scopes], ['harbor_north'])
        self.assertEqual([item.scope_id for item in result.agreements], ['harbor_north'])
        self.assertEqual(self.access('maya').json()['company_id'], 'pacific')

    def test_permission_changes_are_read_on_next_call(self):
        path = self.path / 'users.json'
        users = json.loads(path.read_text())
        maria = next(user for user in users if user['user_id'] == 'maria')
        maria['scope_ids'] = ['harbor_north']
        maria['permission_version'] = 'v2'
        path.write_text(json.dumps(users))
        response = self.access('maria').json()
        self.assertEqual(response['permitted_scope_ids'], ['harbor_north'])
        self.assertEqual(response['permission_version'], 'v2')

    def test_user_id_is_required(self):
        self.assertEqual(self.client.post('/v1/access', json={}).status_code, 422)


if __name__ == '__main__':
    unittest.main()
