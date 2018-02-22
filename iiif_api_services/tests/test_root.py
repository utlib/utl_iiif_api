from rest_framework import status
from test_addons import APIMongoTestCase
import json 


class RootTests(APIMongoTestCase):
    def test_root_endpoint_renders_the_api_documentation(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_endpoint_shows_appropiate_error(self):
        response = self.client.get('/someInvalidURL')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(json.loads(response.content)['error'], 'This API endpoint is invalid.')