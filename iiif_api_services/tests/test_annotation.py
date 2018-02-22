import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.AnnotationModel import Annotation


ANNOTATION_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'annotation', 'annotationMedium.json')
ANNOTATION_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'annotation', 'annotationShort.json')
URL = '/book1/annotation'


class Annotation_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Annotation(label="annotation1", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation/annotation1").save()
        Annotation(label="annotation2", identifier="book1", name="annotation2", ATid="http://example.org/iiif/book1/annotation/annotation2").save()
        Annotation(label="annotation3", identifier="book1", name="annotation3", ATid="http://example.org/iiif/book1/annotation/annotation3").save()

    def test_to_get_all_annotations_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_annotation_of_an_item(self):
        response = self.client.get(URL+"/annotation2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'oa:Annotation')
        self.assertEqual(response.data["label"], 'annotation2')

    def test_an_annotation_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_an_annotation_cannot_be_updated(self):
        response = self.client.put(URL+"/annotation1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_an_annotation_cannot_be_deleted(self):
        response = self.client.delete(URL+"/annotation1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class Annotation_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_an_annotation_can_be_successfully_created_with_no_nested_structures(self):
        data = {"annotation": json.loads(open(ANNOTATION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Annotation.objects.get(name="p0001-image").label, 'Cool annotation')
        self.assertEqual(Annotation.objects.get(name="p0001-image").ATid, settings.IIIF_BASE_URL + "/book1/annotation/p0001-image")

    def test_an_annotation_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"annotation": json.loads(open(ANNOTATION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Annotation.objects.get(name="p0001-image").label, 'Cool annotation')
        self.assertEqual(Annotation.objects.get(name="p0001-image").ATid, settings.IIIF_BASE_URL + "/book1/annotation/p0001-image")
        createdAnnotationID = settings.IIIF_BASE_URL + "/book1/annotation/p0001-image"

    def test_a_duplicate_annotation_cannot_be_created(self):
        data = {"annotation": json.loads(open(ANNOTATION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')

    def test_an_annotation_with_no_id_given_can_be_successfully_created(self):
        data = {"annotation": json.loads(open(ANNOTATION_SHORT).read())}
        del data["annotation"]["@id"]
        response = self.client.post("/UofT/annotation", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Annotation.objects()[0].label, 'Cool annotation')

    def test_an_annotation_cannot_be_created_if_id_does_not_match_with_identifier(self):
        data = {"annotation": json.loads(open(ANNOTATION_SHORT).read())}
        response = self.client.post("/UofT/annotation", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "Annotation identifier must match with the identifier in @id.")


class Annotation_Test_GET(APIMongoTestCase):
    def setUp(self):
        Annotation(label="annotation1", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation/annotation1").save()

    def test_an_annotation_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/annotation/annotation1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Annotation with name 'annotation1' does not exist in identifier 'nonExistingItem'.")

    def test_an_annotation_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingAnnotation")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Annotation with name 'nonExistingAnnotation' does not exist in identifier 'book1'.")

    def test_an_annotation_can_be_viewed(self):
        response = self.client.get("/book1/annotation/annotation1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class Annotation_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        Annotation(label="annotation1", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation/annotation1").save()
        Annotation(label="annotation2", identifier="book1", name="annotation2", ATid="http://example.org/iiif/book1/annotation/annotation2").save()
        Annotation(label="annotation3", identifier="book1", name="annotation3", ATid="http://example.org/iiif/book1/annotation/annotation3").save()

    def test_all_annotations_from_an_item_is_returned(self):
        response = self.client.get("/book1/annotation")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/annotation/annotation1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/annotation/annotation3")

    def test_an_annotation_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/annotation")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class Annotation_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Annotation(label="annotation1", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation/annotation1").save()
        Annotation(label="annotation2", identifier="book1", name="annotation2", ATid="http://example.org/iiif/book1/annotation/annotation2").save()

    def test_an_annotation_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/annotation1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Annotation 'annotation1' from identifier 'book1'.")

    def test_an_annotation_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/annotation/annotation1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Annotation with name 'annotation1' does not exist in identifier 'nonExistingItem'.")

    def test_an_annotation_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingAnnotation")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Annotation with name 'nonExistingAnnotation' does not exist in identifier 'book1'.")

    def test_deleting_an_annotation_will_delete_all_of_its_nested_objects(self):
        data = {"annotation": json.loads(open(ANNOTATION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/p0001-image")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Annotation 'p0001-image' from identifier 'book1'.")



class Annotation_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Annotation(label="annotation1", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation/annotation1", viewingHint="paged").save()
        Annotation(label="annotation2", identifier="book1", name="annotation2", ATid="http://example.org/iiif/book1/annotation/annotation2").save()

    def test_an_annotation_can_be_updated_sucessfully(self):
        data = {"annotation": {"label": "new_annotation1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/annotation1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Annotation.objects.get(name="annotation1").label, 'new_annotation1')
        self.assertEqual(Annotation.objects.get(name="annotation1").viewingHint, 'non-paged')

    def test_an_annotation_that_does_not_exist_cannot_be_updated(self):
        data = {"annotation": {"label": "new_annotation1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingAnnotation", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Annotation with name 'nonExistingAnnotation' does not exist in identifier 'book1'.")

    def test_an_annotation_with_new_id_can_be_updated_successfully(self):
        data = {"annotation": {"@id": "http://example.org/iiif/new_book1/annotation/new_annotation1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/annotation1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Annotation.objects.get(name="new_annotation1").ATid, settings.IIIF_BASE_URL + "/new_book1/annotation/new_annotation1")

