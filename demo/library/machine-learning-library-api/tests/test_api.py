import unittest
from fastapi.testclient import TestClient
from library_api.infer import create_app


class LibraryApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_read_company_information(self):
        response = self.client.post('/v1/company-information', json={
            'company_id': 'harbor', 'permitted_scope_ids': ['harbor_north']})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['company']['company_id'], 'harbor')
        self.assertEqual([item['scope_id'] for item in result['scopes']], ['harbor_north'])
        self.assertEqual(result['agreements'][0]['valid_from'], '2026-09-01')
        self.assertNotIn('harbor_south', response.text)
        self.assertNotIn('pacific', response.text)

    def test_permissions_are_required(self):
        response = self.client.post('/v1/company-information', json={'company_id': 'harbor'})
        self.assertEqual(response.status_code, 422)

    def test_cross_company_terminal_is_rejected(self):
        response = self.client.post('/v1/company-information', json={
            'company_id': 'harbor', 'permitted_scope_ids': ['pacific_north']})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
