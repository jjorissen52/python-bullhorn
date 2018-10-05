import json
import unittest

from bullhorn.api import BullhornClient
from bullhorn.pipeline import execution_pipeline, pre
from bullhorn.api import exceptions


class TestPipelineMethods(unittest.TestCase):

    @classmethod
    def setUp(cls):
        class A(BullhornClient):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            @execution_pipeline(pre=[pre.keep_authenticated])
            def fake_method(self):
                pass

            @execution_pipeline(pre=[pre.clean_api_call_input])
            def fake_method1(self, **kwargs):
                return kwargs

        cls._test_client = A()

    # @unittest.skip('okay this one works')
    def test_keep_authenticated(self):
        self._test_client.fake_method()
        self.assertIsNotNone(self._test_client.auth_details.get('bh_rest_token', None))

    def test_validate_api_call_input(self):
        required_params = 'command', 'method', 'entity', 'select_fields', 'entity_id_str'
        with self.assertRaises(exceptions.APICallError):
            self._test_client.fake_method1()
            self._test_client.fake_method1(method="GET")
            self._test_client.fake_method1(command="search")
            self._test_client.fake_method1(entity="billy")
            self._test_client.fake_method1(select_fields="1,2,3,4")
            self._test_client.fake_method1(entity_id="1")
            self._test_client.fake_method1(query="id:1")
            # should fail due to lack of query argument
            self._test_client.fake_method1(method="GET", command="search", entity="billy",
                                           select_fields="1,2,3,4", entity_id="1")
            # should fail due to lack of entity_id
            self._test_client.fake_method1(method="GET", command="entity", entity="billy",
                                           select_fields="1,2,3,4")

        resulting_params = self._test_client.fake_method1(method="GET", command="entity", entity="billy",
                                                          select_fields="1,2,3,4", entity_id="1")
        for required in required_params:
            self.assertIn(required, resulting_params.keys())


class TestAPICall(unittest.TestCase):

    def test_api_call(self):
        b = BullhornClient()
        response = b.api_call(command='entity', method='GET', entity='Candidate', entity_id=42419)
        response = b.api_call(command='entity', method='GET', entity='Candidate', entity_id=42419, LastName='Okay')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.text)
        self.assertIn('data', response_dict)
