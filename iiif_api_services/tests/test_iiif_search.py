import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from rest_framework_jwt.settings import api_settings


MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'manifest', 'manifestFull.json')


class Search_IIIF_API_Within_Manifest(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")


    def test_to_search_all_matching_resources(self):
        response = self.client.get('/book1/manifest/search/?q=book book2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + '/book1/manifest/search/?q=book%20book2')
        self.assertEqual(len(response.data["resources"]), 2)

    def test_to_search_a_single_matching_resource(self):
        response = self.client.get('/book1/manifest/search/?q=top')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + '/book1/manifest/search/?q=top')
        self.assertEqual(len(response.data["resources"]), 1)

    def test_to_search_no_matching_resource(self):
        response = self.client.get('/book1/manifest/search/?q=nothing')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + '/book1/manifest/search/?q=nothing')
        self.assertEqual(len(response.data["resources"]), 0)


    def test_to_search_a_single_matching_resource_with_motivation(self):
        response = self.client.get('/book1/manifest/search/?q=top&motivation=painting')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + '/book1/manifest/search/?q=top&motivation=painting')
        self.assertEqual(len(response.data["resources"]), 1)

    def test_to_search_a_single_matching_resource_with_invalid_motivation(self):
        response = self.client.get('/book1/manifest/search/?q=top&motivation=invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + '/book1/manifest/search/?q=top&motivation=invalid')
        self.assertEqual(len(response.data["resources"]), 0)


    def test_to_search_a_single_matching_resource_with_missing_query(self):
        response = self.client.get('/book1/manifest/search/?motivation=invalid')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], "The parameter 'q' is required.")


    def test_to_search_a_single_matching_resource_on_non_existing_manifest(self):
        response = self.client.get('/book1123456789/manifest/search/?q=top')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "'book1123456789' does not have a Manifest.")
