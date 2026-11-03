import json
import unittest
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from api_objects.faro.library.input.library_input import LibraryInput
from api_objects.faro.library.output.library_output import LibraryOutput


DATA = Path(__file__).resolve().parents[2] / 'local_data' / 'demo_dataset'


def load_collection(name):
    return json.loads((DATA / f'{name}.json').read_text())


class LibraryObjectsTest(unittest.TestCase):
    def test_request_requires_explicit_permissions(self):
        with self.assertRaises(ValidationError):
            LibraryInput(company_id='harbor')

        request = LibraryInput(company_id='harbor', permitted_scope_ids=[])
        self.assertEqual(request.permitted_scope_ids, [])
        self.assertEqual(LibraryInput.model_validate_json(request.model_dump_json()), request)

    def test_company_fixtures_round_trip_as_api_messages(self):
        for company in load_collection('companies'):
            with self.subTest(company=company['company_id']):
                company_id = company['company_id']
                payload = {'company': company}
                for collection in ['scopes', 'documents', 'agreements']:
                    payload[collection] = [
                        item for item in load_collection(collection)
                        if item['company_id'] == company_id
                    ]
                response = LibraryOutput.model_validate(payload)
                self.assertIsInstance(response.agreements[0].valid_from, date)
                self.assertEqual(response.company.company_id, company_id)
                self.assertEqual(len(response.scopes), 2)
                self.assertNotIn('_id', response.model_dump()['company'])
                self.assertEqual(
                    LibraryOutput.model_validate_json(response.model_dump_json()), response
                )

    def test_invalid_nested_date_is_rejected(self):
        payload = {
            'company': load_collection('companies')[0],
            'scopes': [],
            'documents': [],
            'agreements': [load_collection('agreements')[0]],
        }
        payload['agreements'][0]['valid_from'] = 'not-a-date'
        with self.assertRaises(ValidationError):
            LibraryOutput.model_validate(payload)


if __name__ == '__main__':
    unittest.main()
