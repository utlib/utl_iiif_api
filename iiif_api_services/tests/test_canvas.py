from rest_framework import status
from iiif_api_services.models.CanvasModel import *
from test_addons import MongoTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


URL = '/book1/canvas/'

class CanvasTests(MongoTestCase, APITestCase):

    def setUp(self):
        canvas1 = Canvas(label="canvas1", item="book1", name="canvas1", width=50, height=50).save()

    def test_to_get_all_canvass_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_to_get_a_canvas_of_an_item(self):
        response = self.client.get(URL+"canvas1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], 'sc:Canvas')
        self.assertEqual(response.data["label"], 'canvas1')


    def test_get_all_canvas_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, POST, OPTIONS')


    def test_get_canvas_of_an_item_has_correct_allowed_methods(self):
        response = self.client.get(URL+"canvas1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Allow'], 'GET, PUT, DELETE, OPTIONS')


    def test_a_canvas_cannot_be_created_without_authentication(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_canvas_cannot_be_updated_without_authentication(self):
        response = self.client.put(URL+"canvas1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_canvas_cannot_be_deleted_without_authentication(self):
        response = self.client.delete(URL+"canvas1", {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CanvasTestsWithAuthentication(MongoTestCase, APITestCase):

    allow_database_queries = True
    def setUp(self):
        self.data = {  "context": "http://iiif.io/api/presentation/2/context.json",
                        "type": "sc:Canvas",
                        "label": "canvas1",
                        "height": 50,
                        "width": 50}

        self.user = User.objects.create_user('testadmin', 'foo@bar.de', 'testadminpass')
        self.client.login(username='testadmin', password='testadminpass')
        session = self.client.session
        session['documents_to_share_ids'] = [1]
        session.save()


    def test_a_canvas_can_be_successfully_created_with_authentication(self):
        response = self.client.post(URL, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'canvas1')


    def test_a_canvas_cannot_be_created_with_empty_label(self):
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.post(URL, self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_canvas_can_be_successfully_updated_with_authentication(self):
        canvas1 = Canvas(label="canvas1", item="book1", name="canvas1", width=50, height=50).save()
        self.data["label"] = "new_canvas1"
        response = self.client.put(URL+"canvas1", self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["label"], 'new_canvas1')


    def test_a_canvas_cannot_be_updated_with_empty_label(self):
        canvas1 = Canvas(label="canvas1", item="book1", name="canvas1", width=50, height=50).save()
        self.empty_label_data = self.data
        del self.empty_label_data["label"]
        response = self.client.put(URL+"canvas1", self.empty_label_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["label"], ["This field is required."])


    def test_a_canvas_can_be_deleted_with_authentication(self):
    	canvas1 = Canvas(label="canvas1", item="book1", name="canvas1", width=50, height=50).save()
        response = self.client.delete(URL+"canvas1")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)