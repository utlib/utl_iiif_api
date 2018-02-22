from rest_framework import status
from iiif_api_services.models.ResourceModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
import os

URL = '/book1/res/'

class ResourcesTests(MongoTestCase, APITestCase):

    def setUp(self):
        resource1 = Resource(label="resource1", item="book1", name="resource1", type="img/jpeg").save()

    def test_to_get_all_resources_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_to_get_a_resource_of_an_item(self):
        response = self.client.get(URL+"resource1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'img/jpeg')
        self.assertEqual(response.data["label"], 'resource1')


    def test_get_all_resource_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, OPTIONS')


    def test_get_resource_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL+"resource1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, PUT, DELETE, OPTIONS')


    def test_a_resource_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_resource_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL+"resource1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_resource_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL+"resource1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ResourcesTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "sc:Resource",
                        "label": "resource1",
                        "type": "img/jpeg",
                        "format": "",
                        "resource": None,
                        "res_url": ""}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_resource_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'resource1')


    def test_a_resource_can_be_successfully_updated_with_authentication(self):
        resource1 = Resource(label="resource1", item="book1", name="resource1", type="img/jpeg").save()
        self.data["label"] = "new_resource1"
        response = self.client.put(URL+"resource1", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_resource1')


    def test_a_resource_can_be_deleted_with_authentication(self):
    	resource1 = Resource(label="resource1", item="book1", name="resource1", type="img/jpeg").save()
        response = self.client.delete(URL+"resource1")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)