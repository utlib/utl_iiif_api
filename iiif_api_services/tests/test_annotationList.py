from rest_framework import status
from iiif_api_services.models.AnnotationListModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


URL = '/book1/list/'

class AnnotationListsTests(MongoTestCase, APITestCase):

    def setUp(self):
        annotationList1 = AnnotationList(label="annotationList1", item="book1", name="annotationList1").save()

    def test_to_get_all_annotationLists_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_to_get_a_annotationList_of_an_item(self):
        response = self.client.get(URL+"annotationList1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'sc:AnnotationList')
        self.assertEqual(response.data["label"], 'annotationList1')


    def test_get_all_annotationList_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, OPTIONS')


    def test_get_annotationList_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL+"annotationList1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, PUT, DELETE, OPTIONS')


    def test_a_annotationList_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_annotationList_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL+"annotationList1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_annotationList_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL+"annotationList1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnnotationListsTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "sc:AnnotationList",
                        "label": "annotationList1",}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_annotationList_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'annotationList1')


    def test_a_annotationList_cannot_be_created_with_empty_label(self):
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.post(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_annotationList_can_be_successfully_updated_with_authentication(self):
        annotationList1 = AnnotationList(label="annotationList1", item="book1", name="annotationList1").save()
        self.data["label"] = "new_annotationList1"
        response = self.client.put(URL+"annotationList1", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_annotationList1')


    def test_a_annotationList_cannot_be_updated_with_empty_label(self):
        annotationList1 = AnnotationList(label="annotationList1", item="book1", name="annotationList1").save()
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.put(URL+"annotationList1", self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_annotationList_can_be_deleted_with_authentication(self):
    	annotationList1 = AnnotationList(label="annotationList1", item="book1", name="annotationList1").save()
        response = self.client.delete(URL+"annotationList1")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)