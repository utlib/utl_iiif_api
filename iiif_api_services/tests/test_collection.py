from rest_framework import status
from iiif_api_services.models.CollectionModel import *
from iiif_api_services.models.ManifestModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


URL = '/collections/'

class CollectionsTests(MongoTestCase, APITestCase):

    def setUp(self):
        collection1 = Collection(label="Collection1", name="collection1").save()

    def test_collections_list_top_level_collection_and_allows_POST_method(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, OPTIONS')
        self.assertEqual(response.data["type"], 'sc:Collection')
        self.assertEqual(response.data["label"], 'Organization')

    def test_collections_list_has_1_total_memebers_initially(self):
        response = self.client.get(URL)
        self.assertEqual(response.data["total"], 1)

    def test_collections_list_has_2_total_memebers_after_adding_two_members(self):
        manifest1 = Manifest(label="manifest1", item="manifest1").save()
        response = self.client.get(URL)
        self.assertEqual(response.data["total"], 2)

    def test_collections_list_has_the_correct_canvas_type(self):
        response = self.client.get(URL)
        self.assertEqual(response.data["type"], 'sc:Collection')

    def test_top_level_collection_endpoint_always_redirects_to_root(self):
        response = self.client.get(URL+"Organization/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], '/')

    def test_a_new_collection_can_be_retrieved_successfully(self):
        response = self.client.get(URL+'collection1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'sc:Collection')
        self.assertEqual(response.data["label"], 'Collection1')
        self.assertEqual(response['Allow'], 'GET, PUT, DELETE, OPTIONS')

    def test_a_collection_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_collection_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL+"collection1/", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_collection_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL+"collection1/", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CollectionsTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "sc:Collection",
                        "label": "collection1",}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_collection_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'collection1')


    def test_a_collection_cannot_be_created_with_empty_label(self):
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.post(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_collection_cannot_be_created_with_duplicate_label(self):
        collection1 = Collection(label="collection1", name="collection1").save()
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field must be unique."])


    def test_a_collection_can_be_successfully_updated_with_authentication(self):
        collection1 = Collection(label="collection1", name="collection1").save()
        self.data["label"] = "new_collection1"
        response = self.client.put(URL+"collection1/", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_collection1')


    def test_a_collection_cannot_be_updated_with_empty_label(self):
        collection1 = Collection(label="collection1", name="collection1").save()
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.put(URL+"collection1/", self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_collection_cannot_be_updated_with_duplicate_label(self):
        collection1 = Collection(label="collection1", name="collection1").save()
        collection2 = Collection(label="collection2", name="collection2").save()
        self.new_label_data = self.data
        self.new_label_data["label"] = "collection2"
        response = self.client.put(URL+"collection1/", self.new_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field must be unique."])


    def test_a_collection_can_be_deleted_with_authentication(self):
        response = self.client.delete(URL+"collection1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)