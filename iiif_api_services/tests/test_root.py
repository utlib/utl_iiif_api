from rest_framework import status
from iiif_api_services.models.CollectionModel import *
from test_addons import MongoTestCase


URL = '/'
class RootTests(MongoTestCase):

    def test_root_endpoint_gives_correct_status_message(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_root_endpoint_contains_top_level_collection(self):
        response = self.client.get(URL)
        self.assertEqual(response.data["type"], 'sc:Collection')
        self.assertEqual(response.data["label"], 'Organization')

    def test_root_endpoint_allows_only_GET_method(self):
        response = self.client.get(URL)
        self.assertEqual(response['Allow'], 'GET, OPTIONS')

    def test_root_endpoint_has_no_collections_under_it_initially(self):
        response = self.client.get(URL)
        self.assertEqual(Collection.objects.count(), 0)

    def test_root_endpoint_contains_other_collections_after_adding_two_new_collections(self):
        collection1 = Collection(label="Collection1", name="collection1").save()
        collection2 = Collection(label="Collection2", name="collection2").save()
        response = self.client.get(URL)
        self.assertEqual(len(response.data["collections"]), Collection.objects.count())