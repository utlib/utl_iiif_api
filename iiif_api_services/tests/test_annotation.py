from rest_framework import status
from iiif_api_services.models.AnnotationModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


URL = '/book1/annotation/'

class AnnotationsTests(MongoTestCase, APITestCase):

    def setUp(self):
        annotation1 = Annotation(label="annotation1", item="book1", name="annotation1", on="http://142.150.192.147:8000/book1/canvas/Fghfgh").save()

    def test_to_get_all_annotations_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_to_get_a_annotation_of_an_item(self):
        response = self.client.get(URL+"annotation1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'oa:Annotation')
        self.assertEqual(response.data["label"], 'annotation1')


    def test_get_all_annotation_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, OPTIONS')


    def test_get_annotation_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL+"annotation1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, PUT, DELETE, OPTIONS')


    def test_a_annotation_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_annotation_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL+"annotation1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_annotation_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL+"annotation1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnnotationsTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "label": "annotation1",
                        "on": "http://142.150.192.147:8000/book1/canvas/Fghfgh"}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_annotation_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'annotation1')


    def test_a_annotation_cannot_be_created_with_empty_label(self):
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.post(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_annotation_can_be_successfully_updated_with_authentication(self):
        annotation1 = Annotation(label="annotation1", item="book1", name="annotation1", on="http://142.150.192.147:8000/book1/canvas/Fghfgh").save()
        self.data["label"] = "new_annotation1"
        response = self.client.put(URL+"annotation1", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_annotation1')


    def test_a_annotation_cannot_be_updated_with_empty_label(self):
        annotation1 = Annotation(label="annotation1", item="book1", name="annotation1", on="http://142.150.192.147:8000/book1/canvas/Fghfgh").save()
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.put(URL+"annotation1", self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_annotation_can_be_deleted_with_authentication(self):
    	annotation1 = Annotation(label="annotation1", item="book1", name="annotation1", on="http://142.150.192.147:8000/book1/canvas/Fghfgh").save()
        response = self.client.delete(URL+"annotation1")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


    def test_annotation_on_field_must_be_a_valid_url_on_post(self):
        self.invalid_on_data = self.data
        self.invalid_on_data["on"] = "some_random_text"
        response = self.client.post(URL, self.invalid_on_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["on"], ["Enter a valid URL."])


    def test_annotation_on_field_must_be_a_valid_url_on_post(self):
        self.invalid_on_data = self.data
        annotation1 = Annotation(label="annotation1", item="book1", name="annotation1", on="http://142.150.192.147:8000/book1/canvas/Fghfgh").save()
        self.invalid_on_data["on"] = "some_random_text"
        response = self.client.put(URL+"annotation1", self.invalid_on_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["on"], ["Enter a valid URL."])