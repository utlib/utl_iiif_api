from rest_framework import status
from iiif_api_services.models.ManifestModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


URL = '/book1/manifest/'

class ManifestsTests(MongoTestCase, APITestCase):

    def setUp(self):
        manifest1 = Manifest(label="manifest1", item="book1").save()

    def test_to_get_a_manifest_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'sc:Manifest')
        self.assertEqual(response.data["label"], 'manifest1')


    def test_get_manifest_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, PUT, DELETE, OPTIONS')


    def test_a_manifest_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_manifest_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_manifest_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ManifestsTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "sc:Manifest",
                        "label": "manifest1",}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_manifest_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'manifest1')


    def test_an_item_cannot_have_more_than_one_manifest(self):
        manifest1 = Manifest(label="manifest1", item="book1").save()
        response = self.client.post(URL, self.data)
        self.assertEqual(response.data["error"], "Item already exists")


    def test_a_manifest_cannot_be_created_with_empty_label(self):
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.post(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_manifest_can_be_successfully_updated_with_authentication(self):
        manifest1 = Manifest(label="manifest1", item="book1").save()
        self.data["label"] = "new_manifest1"
        response = self.client.put(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_manifest1')


    def test_a_manifest_cannot_be_updated_with_empty_label(self):
        manifest1 = Manifest(label="manifest1", item="book1").save()
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.put(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_manifest_can_be_deleted_with_authentication(self):
        response = self.client.delete(URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)